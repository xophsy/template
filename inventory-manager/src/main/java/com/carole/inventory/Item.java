package com.carole.inventory;

public class Item {
    private final String vItemName;
    private final double vPrice;
    private int vNumInStock;
    private final int vReorderAmount;

    public Item(String vItemName, double vPrice, int vNumInStock, int vReorderAmount) {
        this.vItemName = vItemName;
        this.vPrice = vPrice;
        this.vNumInStock = vNumInStock;
        this.vReorderAmount = vReorderAmount;
    }

    public Item(String vItemName, double vPrice, int vReorderAmount) {
        this(vItemName, vPrice, vReorderAmount * 2, vReorderAmount);
    }

    public String getItemName() {
        return vItemName;
    }

    public double getPrice() {
        return vPrice;
    }

    public int getNumInStock() {
        return vNumInStock;
    }

    public int getReorderAmount() {
        return vReorderAmount;
    }

    public void reduceStock(int vAmount) {
        if (vAmount < 0) {
            throw new IllegalArgumentException("Amount must be non-negative");
        }
        int vUpdated = vNumInStock - vAmount;
        if (vUpdated < 0) {
            vUpdated = 0;
        }
        vNumInStock = vUpdated;
    }

    public void reorder(int vAmount) {
        if (vAmount < 0) {
            throw new IllegalArgumentException("Amount must be non-negative");
        }
        vNumInStock += vAmount;
    }
}
