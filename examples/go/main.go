// GlobalJiema activation flow in Go (standard library only).
// go run main.go <service> <country>
package main

import (
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"
)

const api = "https://globaljiema.com"

type envelope struct {
	Code int             `json:"code"`
	Msg  string          `json:"msg"`
	Data json.RawMessage `json:"data"`
}

type order struct {
	OrderNo   string `json:"order_no"`
	Status    string `json:"status"`
	Phone     string `json:"phone"`
	Amount    string `json:"amount"`
	SmsCode   string `json:"sms_code"`
	ExpiresAt int64  `json:"expires_at"`
	Sms       []struct {
		Text string `json:"text"`
		Code string `json:"code"`
	} `json:"sms"`
}

var key = os.Getenv("GLOBALJIEMA_API_KEY")

func call(method, path string, fields url.Values, out any) error {
	var req *http.Request
	if method == http.MethodGet {
		req, _ = http.NewRequest(method, api+path+"?"+fields.Encode(), nil)
	} else {
		req, _ = http.NewRequest(method, api+path, strings.NewReader(fields.Encode()))
		req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	}
	req.Header.Set("X-API-Key", key)
	res, err := (&http.Client{Timeout: 45 * time.Second}).Do(req)
	if err != nil {
		return err
	}
	defer res.Body.Close()
	var env envelope
	if err := json.NewDecoder(res.Body).Decode(&env); err != nil {
		return fmt.Errorf("HTTP %d", res.StatusCode)
	}
	if env.Code != 1 {
		return fmt.Errorf("api error: %s", env.Msg)
	}
	return json.Unmarshal(env.Data, out)
}

func main() {
	if key == "" || len(os.Args) < 3 {
		fmt.Println("usage: GLOBALJIEMA_API_KEY=... go run main.go <service> <country>")
		os.Exit(1)
	}
	service, country := os.Args[1], os.Args[2]

	var q struct {
		Operators []struct {
			Operator string `json:"operator"`
			Price    string `json:"price"`
		} `json:"operators"`
	}
	if err := call("GET", "/api/activation/quote", url.Values{"service": {service}, "country": {country}}, &q); err != nil {
		panic(err)
	}
	if len(q.Operators) == 0 {
		fmt.Println("no numbers right now")
		return
	}
	op := q.Operators[0]

	b := make([]byte, 16)
	rand.Read(b)
	var a struct {
		Order order `json:"order"`
	}
	err := call("POST", "/api/activation/allocate", url.Values{
		"service": {service}, "country": {country}, "operator": {op.Operator},
		"expected_price": {op.Price}, "idempotency_key": {hex.EncodeToString(b)},
	}, &a)
	if err != nil {
		panic(err)
	}
	fmt.Printf("Number %s ($%s)\n", a.Order.Phone, a.Order.Amount)

	for i := 0; i < 120; i++ {
		time.Sleep(5 * time.Second)
		var p struct {
			Order order `json:"order"`
		}
		if err := call("POST", "/api/activation/poll", url.Values{"order_no": {a.Order.OrderNo}}, &p); err != nil {
			continue
		}
		if len(p.Order.Sms) > 0 {
			fmt.Println("Code:", p.Order.SmsCode, "-", p.Order.Sms[len(p.Order.Sms)-1].Text)
			return
		}
	}
	var c struct {
		Order order `json:"order"`
	}
	_ = call("POST", "/api/activation/cancel", url.Values{"order_no": {a.Order.OrderNo}}, &c)
	fmt.Println("No SMS - cancelled and refunded")
}
