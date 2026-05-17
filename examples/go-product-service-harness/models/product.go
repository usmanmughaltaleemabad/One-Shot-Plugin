package models

import "time"

// Product represents a product in the catalog.
type Product struct {
	ID          string    `json:"id"`
	Name        string    `json:"name"`
	Description string    `json:"description"`
	Price       float64   `json:"price"`
	Category    string    `json:"category"`
	Stock       int       `json:"stock"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
}

// ProductFilter represents query filters for product search.
type ProductFilter struct {
	Category string
	MinPrice float64
	MaxPrice float64
	Search   string
	Page     int
	PageSize int
}
