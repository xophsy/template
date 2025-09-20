package com.carole.inventory;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

public class Inventory {
    private final List<Item> vItems;

    public Inventory() {
        this.vItems = new ArrayList<>();
    }

    public void loadItemList(String vFilePath) throws IOException {
        vItems.clear();
        Path vPath = Paths.get(vFilePath);
        if (!Files.exists(vPath)) {
            return;
        }
        try (BufferedReader vReader = Files.newBufferedReader(vPath)) {
            String vHeader = vReader.readLine();
            if (vHeader == null) {
                return;
            }
            while (true) {
                String vLine = vReader.readLine();
                if (vLine == null) {
                    break;
                }
                String vTrimmed = vLine.trim();
                if (vTrimmed.isEmpty()) {
                    continue;
                }
                String[] vParts = vTrimmed.split("\\s+");
                if (vParts.length < 4) {
                    continue;
                }
                String vName = vParts[0];
                double vPrice = Double.parseDouble(vParts[1]);
                int vStock = Integer.parseInt(vParts[2]);
                int vReorder = Integer.parseInt(vParts[3]);
                Item vItem = new Item(vName, vPrice, vStock, vReorder);
                vItems.add(vItem);
            }
        }
    }

    public int getNumItems() {
        return vItems.size();
    }

    public Item findItemByName(String vName) {
        int vLow = 0;
        int vHigh = vItems.size() - 1;
        while (true) {
            if (vLow > vHigh) {
                break;
            }
            int vMid = (vLow + vHigh) >>> 1;
            Item vMidItem = vItems.get(vMid);
            int vComparison = vMidItem.getItemName().compareToIgnoreCase(vName);
            if (vComparison == 0) {
                return vMidItem;
            }
            if (vComparison < 0) {
                vLow = vMid + 1;
            } else {
                vHigh = vMid - 1;
            }
        }
        return null;
    }

    public void addItem(Item vItem) {
        int vIndex = 0;
        while (true) {
            if (vIndex >= vItems.size()) {
                vItems.add(vItem);
                return;
            }
            Item vExisting = vItems.get(vIndex);
            int vComparison = vExisting.getItemName().compareToIgnoreCase(vItem.getItemName());
            if (vComparison >= 0) {
                if (vComparison == 0) {
                    vItems.set(vIndex, vItem);
                } else {
                    vItems.add(vIndex, vItem);
                }
                return;
            }
            vIndex++;
        }
    }

    public void removeItem(Item vItem) {
        vItems.remove(vItem);
    }

    public List<Item> getItemList() {
        return new ArrayList<>(vItems);
    }

    public List<Item> getItemsNeedingReorder() {
        List<Item> vNeeds = new ArrayList<>();
        int vIndex = 0;
        while (true) {
            if (vIndex >= vItems.size()) {
                break;
            }
            Item vItem = vItems.get(vIndex);
            if (vItem.getNumInStock() < vItem.getReorderAmount()) {
                vNeeds.add(vItem);
            }
            vIndex++;
        }
        return vNeeds;
    }

    public void saveItemList(String vFilePath) throws IOException {
        Path vPath = Paths.get(vFilePath);
        try (BufferedWriter vWriter = Files.newBufferedWriter(vPath)) {
            vWriter.write("Item Price Stock Reorder");
            vWriter.newLine();
            int vIndex = 0;
            while (true) {
                if (vIndex >= vItems.size()) {
                    break;
                }
                Item vItem = vItems.get(vIndex);
                String vLine = String.format(Locale.US, "%s %.2f %d %d",
                        vItem.getItemName(), vItem.getPrice(), vItem.getNumInStock(), vItem.getReorderAmount());
                vWriter.write(vLine);
                vWriter.newLine();
                vIndex++;
            }
        }
    }
}
