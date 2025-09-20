package com.carole.inventory;

import java.io.IOException;
import java.util.List;
import java.util.Locale;
import java.util.Scanner;

public class InventoryManagerApp {
    private static final String VINVENTORY_FILE_PATH = "inventory-manager/inventory-data.txt";

    public static void main(String[] vArgs) {
        Inventory vInventory = new Inventory();
        Scanner vScanner = new Scanner(System.in);
        String vFilePath = VINVENTORY_FILE_PATH;
        if (vArgs != null && vArgs.length > 0 && vArgs[0] != null && !vArgs[0].trim().isEmpty()) {
            vFilePath = vArgs[0];
        }
        try {
            vInventory.loadItemList(vFilePath);
        } catch (IOException vEx) {
            System.out.println("Unable to load inventory file: " + vEx.getMessage());
        }
        boolean vShouldExit = false;
        while (true) {
            System.out.println();
            System.out.println("Inventory Manager");
            System.out.println("F) Find Item");
            System.out.println("A) Add Item");
            System.out.println("L) List All Items");
            System.out.println("N) Show Needed Reorders");
            System.out.println("Q) Quit");
            System.out.print("Select an option: ");
            String vChoiceInput = vScanner.nextLine().trim().toUpperCase(Locale.US);
            if (vChoiceInput.isEmpty()) {
                System.out.println("Please enter a menu option.");
                continue;
            }
            char vChoice = vChoiceInput.charAt(0);
            if (vChoice == 'Q') {
                vShouldExit = true;
                break;
            } else if (vChoice == 'F') {
                System.out.print("Enter the item name: ");
                String vItemName = vScanner.nextLine().trim();
                if (vItemName.isEmpty()) {
                    System.out.println("Item name cannot be empty.");
                } else {
                    Item vFoundItem = vInventory.findItemByName(vItemName);
                    if (vFoundItem == null) {
                        System.out.println("Item not found.");
                    } else {
                        System.out.printf("%-30s %10s %10s %12s%n", "Item", "Price", "In Stock", "Reorder");
                        System.out.printf(Locale.US, "%-30s %10.2f %10d %12d%n", vFoundItem.getItemName(),
                                vFoundItem.getPrice(), vFoundItem.getNumInStock(), vFoundItem.getReorderAmount());
                        while (true) {
                            System.out.println();
                            System.out.println("S) Enter Sale");
                            System.out.println("R) Reorder");
                            System.out.println("D) Delete");
                            System.out.println("C) Cancel");
                            System.out.print("Select an option: ");
                            String vSubInput = vScanner.nextLine().trim().toUpperCase(Locale.US);
                            if (vSubInput.isEmpty()) {
                                System.out.println("Please choose a submenu option.");
                                continue;
                            }
                            char vSubChoice = vSubInput.charAt(0);
                            if (vSubChoice == 'S') {
                                while (true) {
                                    System.out.print("Enter quantity sold: ");
                                    String vQuantityInput = vScanner.nextLine().trim();
                                    try {
                                        int vQuantity = Integer.parseInt(vQuantityInput);
                                        if (vQuantity < 0) {
                                            System.out.println("Quantity must be non-negative.");
                                            continue;
                                        }
                                        vFoundItem.reduceStock(vQuantity);
                                        System.out.println("Sale recorded.");
                                        System.out.printf(Locale.US, "Updated stock: %d%n", vFoundItem.getNumInStock());
                                        break;
                                    } catch (NumberFormatException vEx) {
                                        System.out.println("Please enter a valid whole number.");
                                    }
                                }
                                break;
                            } else if (vSubChoice == 'R') {
                                while (true) {
                                    System.out.print("Enter reorder quantity: ");
                                    String vQuantityInput = vScanner.nextLine().trim();
                                    try {
                                        int vQuantity = Integer.parseInt(vQuantityInput);
                                        if (vQuantity < 0) {
                                            System.out.println("Quantity must be non-negative.");
                                            continue;
                                        }
                                        vFoundItem.reorder(vQuantity);
                                        System.out.println("Reorder recorded.");
                                        System.out.printf(Locale.US, "Updated stock: %d%n", vFoundItem.getNumInStock());
                                        break;
                                    } catch (NumberFormatException vEx) {
                                        System.out.println("Please enter a valid whole number.");
                                    }
                                }
                                break;
                            } else if (vSubChoice == 'D') {
                                vInventory.removeItem(vFoundItem);
                                System.out.println("Item deleted from inventory.");
                                break;
                            } else if (vSubChoice == 'C') {
                                System.out.println("Cancelled.");
                                break;
                            } else {
                                System.out.println("Invalid submenu selection.");
                            }
                        }
                    }
                }
            } else if (vChoice == 'A') {
                Item vNewItem = createItem(vScanner);
                vInventory.addItem(vNewItem);
                System.out.println("Item added to inventory.");
            } else if (vChoice == 'L') {
                List<Item> vItems = vInventory.getItemList();
                if (vItems.isEmpty()) {
                    System.out.println("No items in inventory.");
                } else {
                    System.out.printf("%-30s %10s %10s %12s%n", "Item", "Price", "In Stock", "Reorder");
                    int vIndex = 0;
                    while (true) {
                        if (vIndex >= vItems.size()) {
                            break;
                        }
                        Item vItem = vItems.get(vIndex);
                        System.out.printf(Locale.US, "%-30s %10.2f %10d %12d%n", vItem.getItemName(), vItem.getPrice(),
                                vItem.getNumInStock(), vItem.getReorderAmount());
                        vIndex++;
                    }
                }
            } else if (vChoice == 'N') {
                List<Item> vItemsNeedingReorder = vInventory.getItemsNeedingReorder();
                if (vItemsNeedingReorder.isEmpty()) {
                    System.out.println("No items need reordering.");
                } else {
                    System.out.printf("%-30s %10s %10s %12s%n", "Item", "Price", "In Stock", "Reorder");
                    int vIndex = 0;
                    while (true) {
                        if (vIndex >= vItemsNeedingReorder.size()) {
                            break;
                        }
                        Item vItem = vItemsNeedingReorder.get(vIndex);
                        System.out.printf(Locale.US, "%-30s %10.2f %10d %12d%n", vItem.getItemName(), vItem.getPrice(),
                                vItem.getNumInStock(), vItem.getReorderAmount());
                        vIndex++;
                    }
                }
            } else {
                System.out.println("Invalid menu selection.");
            }
            if (!askToContinue(vScanner)) {
                break;
            }
        }
        try {
            vInventory.saveItemList(vFilePath);
        } catch (IOException vEx) {
            System.out.println("Unable to save inventory file: " + vEx.getMessage());
        }
        if (vShouldExit) {
            System.out.println("Goodbye!");
        } else {
            System.out.println("Thank you for using the Inventory Manager.");
        }
        vScanner.close();
    }

    private static Item createItem(Scanner vScanner) {
        String vItemName;
        while (true) {
            System.out.print("Enter the item name: ");
            vItemName = vScanner.nextLine().trim();
            if (!vItemName.isEmpty()) {
                break;
            }
            System.out.println("Item name cannot be empty.");
        }
        double vPrice;
        while (true) {
            System.out.print("Enter the price: ");
            String vPriceInput = vScanner.nextLine().trim();
            try {
                vPrice = Double.parseDouble(vPriceInput);
                if (vPrice < 0) {
                    System.out.println("Price must be non-negative.");
                    continue;
                }
                break;
            } catch (NumberFormatException vEx) {
                System.out.println("Please enter a valid number.");
            }
        }
        int vReorderAmount;
        while (true) {
            System.out.print("Enter the reorder amount: ");
            String vReorderInput = vScanner.nextLine().trim();
            try {
                vReorderAmount = Integer.parseInt(vReorderInput);
                if (vReorderAmount <= 0) {
                    System.out.println("Reorder amount must be greater than zero.");
                    continue;
                }
                break;
            } catch (NumberFormatException vEx) {
                System.out.println("Please enter a valid whole number.");
            }
        }
        return new Item(vItemName, vPrice, vReorderAmount);
    }

    private static boolean askToContinue(Scanner vScanner) {
        while (true) {
            System.out.print("Would you like to perform another action? (Y/N): ");
            String vResponse = vScanner.nextLine().trim();
            if (vResponse.equalsIgnoreCase("Y")) {
                return true;
            }
            if (vResponse.equalsIgnoreCase("N")) {
                return false;
            }
            System.out.println("Please respond with Y or N.");
        }
    }
}
