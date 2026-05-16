package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"sync"
	"time"
)

// Order represents a trading order
type Order struct {
	ID        string    `json:"id"`
	Symbol    string    `json:"symbol"`
	Quantity  int       `json:"quantity"`
	Price     float64   `json:"price"`
	Type      string    `json:"type"`
	Status    string    `json:"status"`
	CreatedAt time.Time `json:"created_at"`
}

// OrderStore manages orders in memory
type OrderStore struct {
	mu     sync.RWMutex
	orders map[string]Order
}

var store = OrderStore{
	orders: make(map[string]Order),
}

// Health check endpoint
func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
}

// Create order endpoint
func createOrderHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var order Order
	if err := json.NewDecoder(r.Body).Decode(&order); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}

	order.ID = fmt.Sprintf("order_%d", time.Now().UnixNano())
	order.Status = "pending"
	order.CreatedAt = time.Now()

	store.mu.Lock()
	store.orders[order.ID] = order
	store.mu.Unlock()

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(order)
}

// List orders endpoint
func listOrdersHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	store.mu.RLock()
	orders := make([]Order, 0, len(store.orders))
	for _, order := range store.orders {
		orders = append(orders, order)
	}
	store.mu.RUnlock()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(orders)
}

// Get order endpoint
func getOrderHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	id := r.URL.Query().Get("id")
	if id == "" {
		http.Error(w, "Missing id parameter", http.StatusBadRequest)
		return
	}

	store.mu.RLock()
	order, exists := store.orders[id]
	store.mu.RUnlock()

	if !exists {
		http.Error(w, "Order not found", http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(order)
}

func main() {
	http.HandleFunc("/health", healthHandler)
	http.HandleFunc("/orders/create", createOrderHandler)
	http.HandleFunc("/orders/list", listOrdersHandler)
	http.HandleFunc("/orders/get", getOrderHandler)

	fmt.Println("Trading bot API starting on :8080")
	if err := http.ListenAndServe(":8080", nil); err != nil {
		log.Fatal(err)
	}
}
