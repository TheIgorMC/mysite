using System.Data.SqlClient;
using System.Data.SQLite;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using System.Windows.Forms;
using CsvHelper;
using System.IO;
using CsvHelper.Configuration;
using CsvHelper.TypeConversion;
using System.Globalization;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;


namespace EleStockManager
{
    public partial class Form1 : Form
    {
        Globals globals = new Globals();
        Functions functions = new Functions();
        DBhandler handler = new DBhandler();

        private void ApplyFilters()
        {
            // Parse the ID if present; otherwise, set it to zero
            int.TryParse(IDsearchTextBox.Text, out int componentId);

            // Get the values from other TextBoxes, using ToLower() and defaulting to an empty string if empty
            string manufCode = producerTextBox.Text.ToLower();
            string sellerCode = supplierTextBox.Text.ToLower();
            string type = typeTextBox.Text.ToLower();
            string value = valueTextBox.Text.ToLower();
            string package = packageTextBox.Text.ToLower();

            // Call filterElComps with the values from the TextBoxes
            globals.viewerElComps = functions.filterElComps(globals.elComps, componentId, manufCode, sellerCode, type, value, package);

            // Update the viewerDataGrid with the filtered results
            viewerDataGrid.DataSource = null;
            viewerDataGrid.DataSource = globals.viewerElComps;
        }

        public Form1()
        {
            InitializeComponent();
        }

        private void Form1_Load(object sender, EventArgs e)
        {

            globals.readElComp();
            globals.readOrders();
            globals.readBoards();
            globals.readJobs();


            functions.updateQuantities(globals.elComps, globals.orders, globals.boards);
            foreach (var comp in globals.elComps)
            {
                globals.UpdateComponentInDB(comp);
            }


            jobBoardCombo.Items.Clear();
            foreach (var board in globals.boards)
            {
                string boardDisplay = $"{board.Name} - V{board.Version}";
                jobBoardCombo.Items.Add(new { Text = boardDisplay, Value = board.BoardId });            }
            jobBoardCombo.DisplayMember = "Text";
            jobBoardCombo.ValueMember = "Value";
            jobStatusCombo.Items.Clear();
            jobStatusCombo.Items.AddRange(new string[] { "Pending", "Preparing", "In progress", "Completed" });
            jobInsertButton.Enabled = true;
            jobUpdateButton.Enabled = false;
            usePnpForJobCheck.Enabled = true;
            jobIDBox.ReadOnly = false;
            jobBoardCombo.Enabled = true;


            viewerDataGrid.DataSource = null;
            globals.viewerElComps = globals.elComps;
            viewerDataGrid.DataSource = globals.viewerElComps;

            orderViewer.DataSource = null;
            orderViewer.DataSource = globals.orders;

            boardListView.DataSource = null;
            boardListView.DataSource = globals.boards;

            jobViewer.DataSource = null;
            var jobViewModelList = globals.jobs.Select(job => new JobViewModel
            {
                JobId = job.JobId,
                BoardName = globals.boards.FirstOrDefault(b => b.BoardId == job.BoardId)?.Name + " - V" + globals.boards.FirstOrDefault(b => b.BoardId == job.BoardId)?.Version,
                Quantity = job.Quantity,
                UsePnp = job.UsePnp,
                Status = job.Status,
                DueDate = job.DueDate
            }).ToList();
            jobViewer.DataSource = jobViewModelList;


            addBoardIDText.Text = (globals.boards.Count + 1).ToString();
            addIDtext.Text = (globals.elComps.Count + 1).ToString();
            jobIDBox.Text = (globals.jobs.Count + 1).ToString();

        }

        private void smartSearchTextBox_TextChanged(object sender, EventArgs e)
        {            
            viewerDataGrid.DataSource = null;
            Globals.globalFilter = smartSearchTextBox.Text.ToLower();
            if (smartSearchTextBox.Text.Length > 0) viewerDataGrid.DataSource = functions.filterElComps(globals.elComps);
            else viewerDataGrid.DataSource = globals.elComps;
        }

        private void updateViewerButton_Click(object sender, EventArgs e)
        {

        }
        
        private void loadOrderButton_Click(object sender, EventArgs e)
        {

            string filePath = "";

            if (Globals.orderFilePath == "")
            {
                openOrderCSV.ShowDialog(this);
                filePath = openOrderCSV.FileName;
                Globals.orderFilePath = filePath;
            }
            else filePath = Globals.orderFilePath;
            
            
            if (filePath.Contains("LCSC"))
            {
                var compList = functions.ReadLcscOrderItems(filePath);
                DateTime orderDate = orderDateInsert.Value.Date;

                string onlyName = openOrderCSV.SafeFileName.Substring(0, openOrderCSV.SafeFileName.Length - 4);
                var parts = onlyName.Split('_');

                // Assuming the last three parts represent YEAR, MONTH, DAY
                if (parts.Length >= 4)
                {
                    int year = int.Parse(parts[parts.Length - 3]);
                    int month = int.Parse(parts[parts.Length - 2]);
                    int day = int.Parse(parts[parts.Length - 1]);

                    orderDate = new DateTime(year, month, day);
                    orderDateInsert.Value = orderDate;
                }

                Order order = new Order();
                if (globals.orders.Count > 0)
                    order.OrderId = globals.orders.Max(o => o.OrderId) + 1;
                else
                    order.OrderId = 1;

                order.Supplier = "LCSC";
                order.Status = "Complete";
                order.OrderDate = orderDate;
                order.ComponentIds = new List<int>();
                order.Quantities = new List<int>();

                List<OrderComp> orderComps = new List<OrderComp>();
                List<OrderComponent> orderComponents = new List<OrderComponent>();

                foreach (var comp in compList)
                {
                    // Check if the component exists in the database
                    int idOut = globals.elComps
                                        .Where(elComp => elComp.ManufacturerCode == comp.ManufacturerPartNumber)
                                        .Select(elComp => elComp.ComponentId)
                                        .FirstOrDefault();

                    // If component does not exist, redirect user to input the missing component
                    if (idOut == 0)
                    {
                        // Save the current component for input
                        Globals.currentLCSCMissingComponent = comp; // Store the missing component globally (or in a class variable)

                        addSupplierCodeText.Text = Globals.currentLCSCMissingComponent.LcscPartNumber;
                        addMakerCodeText.Text = Globals.currentLCSCMissingComponent.ManufacturerPartNumber;
                        addMakerText.Text = Globals.currentLCSCMissingComponent.Manufacturer;
                        addPackageText.Text = Globals.currentLCSCMissingComponent.Package;
                        addPriceText.Text = Globals.currentLCSCMissingComponent.UnitPrice.ToString("F2"); // Format price to 2 decimal places
                        addValueText.Text = ""; // You can set the appropriate value if known, or leave it for user input
                        addTypeText.Text = "";  // Similarly, set or leave empty
                        addPnpFootprintText.Text = "";  // Set SMD footprint if needed, or leave empty
                        addIDtext.Text = (globals.elComps.Max(elcomp => elcomp.ComponentId) + 1).ToString(); // Generate new ID
                        addSupplierText.Text = "LCSC";  // Since you're working with LCSC data
                        addQuantityText.Text = Globals.currentLCSCMissingComponent.OrderQuantity.ToString();

                        // Switch to the tab that allows the user to fill missing component details
                        tabControl1.SelectTab(mainPage); // Switch to the tab for user input

                        // Pause execution until the user finishes input (the input tab will handle resuming execution)
                        return;  // Break execution here and wait for the user to add the missing component
                    }

                    // Existing component logic continues...
                    double resultPrice = comp.UnitPrice;
                    if (!Globals.isCurrencyEuros)
                        resultPrice *= 0.92;

                    if (idOut != 0)
                    {
                        globals.elComps.FirstOrDefault(elcomp => elcomp.ComponentId == idOut).QuantityLeft += comp.OrderQuantity;
                        globals.elComps.FirstOrDefault(elcomp => elcomp.ComponentId == idOut).Price = Math.Round(resultPrice, 3);
                    }

                    order.ComponentIds.Add(idOut);
                    order.Quantities.Add(comp.OrderQuantity);
                    order.TotalCost += Math.Round(comp.UnitPrice * comp.OrderQuantity, 2);

                    orderComps.Add(new OrderComp
                    {
                        ComponentID = idOut,
                        SellerCode = comp.LcscPartNumber,
                        Quantity = comp.OrderQuantity,
                        UnitPrice = Math.Round(comp.UnitPrice, 4),
                        TotalPrice = Math.Round(comp.UnitPrice * comp.OrderQuantity, 2)
                    });

                    orderComponents.Add(new OrderComponent
                    {
                        ComponentId = idOut,
                        Quantity = comp.OrderQuantity,
                        Price = Math.Round(comp.UnitPrice, 4)
                    });
                }

                globals.selOrderComps.Clear();
                globals.selOrderComps = orderComps;

                globals.orderComponents.Clear();
                globals.orderComponents = orderComponents;

                globals.orders.Add(order);

                orderViewer.DataSource = null;
                orderComponentsViewer.DataSource = null;
                orderViewer.DataSource = globals.orders;
                orderComponentsViewer.DataSource = globals.selOrderComps;

                Globals.orderFilePath = "";
            }
            else if (filePath.Contains("MOUSER"))
            {
                var compList = functions.ReadMouserOrderItems(filePath);
                DateTime orderDate = orderDateInsert.Value.Date;

                string onlyName = openOrderCSV.SafeFileName.Substring(0, openOrderCSV.SafeFileName.Length - 4);
                var parts = onlyName.Split('_');

                // Assuming the last three parts represent YEAR, MONTH, DAY
                if (parts.Length >= 4)
                {
                    int year = int.Parse(parts[parts.Length - 3]);
                    int month = int.Parse(parts[parts.Length - 2]);
                    int day = int.Parse(parts[parts.Length - 1]);

                    orderDate = new DateTime(year, month, day);
                    orderDateInsert.Value = orderDate;
                }

                Order order = new Order();
                if (globals.orders.Count > 0)
                    order.OrderId = globals.orders.Max(o => o.OrderId) + 1;
                else
                    order.OrderId = 1;

                order.Supplier = "MOUSER";
                order.Status = "Complete";
                order.OrderDate = orderDate;
                order.ComponentIds = new List<int>();
                order.Quantities = new List<int>();

                List<OrderComp> orderComps = new List<OrderComp>();
                List<OrderComponent> orderComponents = new List<OrderComponent>();

                foreach (var comp in compList)
                {
                    // Check if the component exists in the database
                    int idOut = globals.elComps
                                        .Where(elComp => elComp.ManufacturerCode == comp.ManufacturerPartNumber)
                                        .Select(elComp => elComp.ComponentId)
                                        .FirstOrDefault();

                    // If component does not exist, redirect user to input the missing component
                    if (idOut == 0)
                    {
                        // Save the current component for input
                        Globals.currentMouserMissingComponent = comp; // Store the missing component globally (or in a class variable)

                        addSupplierCodeText.Text = Globals.currentMouserMissingComponent.MouserPartNumber;
                        addMakerCodeText.Text = Globals.currentMouserMissingComponent.ManufacturerPartNumber;
                        addMakerText.Text = Globals.currentMouserMissingComponent.Manufacturer;
                        addPriceText.Text = Globals.currentMouserMissingComponent.UnitPrice.ToString("F2");
                        addIDtext.Text = (globals.elComps.Max(elcomp => elcomp.ComponentId) + 1).ToString();
                        addQuantityText.Text = Globals.currentMouserMissingComponent.OrderQuantity.ToString();
                        addSupplierText.Text = "MOUSER";

                        tabControl1.SelectTab(mainPage);
                        return;
                    }

                    double resultPrice = comp.UnitPrice;
                    if (!Globals.isCurrencyEuros)
                        resultPrice *= 0.92;

                    if (idOut != 0)
                    {
                        globals.elComps.FirstOrDefault(elcomp => elcomp.ComponentId == idOut).QuantityLeft += comp.OrderQuantity;
                        globals.elComps.FirstOrDefault(elcomp => elcomp.ComponentId == idOut).Price = Math.Round(resultPrice, 3);
                    }

                    order.ComponentIds.Add(idOut);
                    order.Quantities.Add(comp.OrderQuantity);
                    order.TotalCost += Math.Round(comp.UnitPrice * comp.OrderQuantity, 2);

                    orderComps.Add(new OrderComp
                    {
                        ComponentID = idOut,
                        SellerCode = comp.MouserPartNumber,
                        Quantity = comp.OrderQuantity,
                        UnitPrice = Math.Round(comp.UnitPrice, 4),
                        TotalPrice = Math.Round(comp.UnitPrice * comp.OrderQuantity, 2)
                    });

                    orderComponents.Add(new OrderComponent
                    {
                        ComponentId = idOut,
                        Quantity = comp.OrderQuantity,
                        Price = Math.Round(comp.UnitPrice, 4)
                    });
                }

                globals.selOrderComps.Clear();
                globals.selOrderComps = orderComps;

                globals.orderComponents.Clear();
                globals.orderComponents = orderComponents;

                globals.orders.Add(order);

                orderViewer.DataSource = null;
                orderComponentsViewer.DataSource = null;
                orderViewer.DataSource = globals.orders;
                orderComponentsViewer.DataSource = globals.selOrderComps;

                Globals.orderFilePath = "";
            }

        }

        private void addButton_Click(object sender, EventArgs e)
        {
            // Perform validation on all required fields
            if (string.IsNullOrWhiteSpace(addIDtext.Text) ||
                string.IsNullOrWhiteSpace(addSupplierCodeText.Text) ||
                string.IsNullOrWhiteSpace(addMakerCodeText.Text) ||
                string.IsNullOrWhiteSpace(addMakerText.Text) ||
                string.IsNullOrWhiteSpace(addPackageText.Text) ||
                string.IsNullOrWhiteSpace(addPriceText.Text) ||
                string.IsNullOrWhiteSpace(addTypeText.Text))
            {
                MessageBox.Show("Please fill in all required fields before adding the component.", "Missing Information", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;  // Exit the function if validation fails
            }

            // Validate numeric fields
            if (!int.TryParse(addIDtext.Text, out int componentId) ||
                !double.TryParse(addPriceText.Text, out double price))
            {
                MessageBox.Show("Please ensure the ID and Price fields are correctly filled with numeric values.", "Invalid Input", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;  // Exit the function if numeric validation fails
            }

            // Determine the quantity left: use OrderQuantity from the missing component if present, otherwise default to 0 for manual additions
            int quantityLeft = 0;
            if (Globals.currentLCSCMissingComponent != null)
            {
                quantityLeft = Globals.currentLCSCMissingComponent.OrderQuantity;
            }
            else if (Globals.currentMouserMissingComponent != null)
            {
                quantityLeft = Globals.currentMouserMissingComponent.OrderQuantity;
            }
            else if (!int.TryParse(addQuantityText.Text, out quantityLeft)) // Check for quantity if manually added
            {
                MessageBox.Show("Please enter a valid quantity if manually adding a component.", "Invalid Input", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            // Create a new ElComp object based on the input fields
            ElComp newComponent = new ElComp
            {
                ComponentId = componentId,
                SellerCode = addSupplierCodeText.Text,
                Seller = addSupplierText.Text,
                ManufacturerCode = addMakerCodeText.Text,
                Manufacturer = addMakerText.Text,
                Package = addPackageText.Text,
                Price = price,
                SmdFootprint = addPnpFootprintText.Text,
                ProductType = addTypeText.Text,
                Value = addValueText.Text,
                QuantityLeft = quantityLeft  // Use the quantity from the order or default for manual addition
            };

            // Add the new component to the global elComps list
            globals.elComps.Add(newComponent);

            // Insert the new component into the database
            globals.InsertComponent(newComponent);

            // Check if it was a missing component from LCSC, MOUSER, or a manual addition
            if (Globals.currentLCSCMissingComponent != null && !string.IsNullOrEmpty(Globals.currentLCSCMissingComponent.LcscPartNumber))
            {
                // If it's an LCSC missing component, clear it and switch back to the purchase page tab
                Globals.currentLCSCMissingComponent = null;
                tabControl1.SelectTab(purchasePage);

                // Resume the order loading process
                loadOrderButton_Click(sender, e);
            }
            else if (Globals.currentMouserMissingComponent != null && !string.IsNullOrEmpty(Globals.currentMouserMissingComponent.MouserPartNumber))
            {
                // If it's a MOUSER missing component, clear it and switch back to the purchase page tab
                Globals.currentMouserMissingComponent = null;
                tabControl1.SelectTab(purchasePage);

                // Resume the order loading process
                loadOrderButton_Click(sender, e);
            }
            else
            {

                MessageBox.Show("Component added successfully.", "Success", MessageBoxButtons.OK, MessageBoxIcon.Information);
                
            }

            addIDtext.Clear();
            addSupplierCodeText.Clear();
            addSupplierText.Clear();
            addMakerCodeText.Clear();
            addMakerText.Clear();
            addPackageText.Clear();
            addPriceText.Clear();
            addTypeText.Clear();
            addValueText.Clear();
            addPnpFootprintText.Clear();
            addQuantityText.Clear();

            // Update the DataGridView with the latest components list
            viewerDataGrid.DataSource = null;
            viewerDataGrid.DataSource = globals.viewerElComps;
        }

        private void updateOrderButton_Click(object sender, EventArgs e)
        {

            if(globals.orders.Count >0)
            {
                globals.insertOrder(globals.orders.Last());
                globals.orders.Clear();

                globals.readOrders();
                orderViewer.DataSource = null;
                orderViewer.DataSource = globals.orders;

                globals.orderComponents.Clear();

                MessageBox.Show("Order added successfully.", "Success", MessageBoxButtons.OK, MessageBoxIcon.Information);

            }
        }
        
        private void addBoardsButton_Click(object sender, EventArgs e)
        {
            // Check if required fields are filled
            if (string.IsNullOrWhiteSpace(addBoardIDText.Text) ||
                string.IsNullOrWhiteSpace(addBoardNameText.Text) ||
                string.IsNullOrWhiteSpace(addBoardVersionText.Text))
            {
                MessageBox.Show("Please fill in all required fields (Board ID, Name, and Version) before adding the board.", "Missing Information", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return; // Exit the function if validation fails
            }

            // Check if the board components list is empty
            if (globals.boardcomps.Count == 0)
            {
                MessageBox.Show("No components have been added to the board. Please add components before creating the board.", "No Components", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return; // Exit the function if there are no components
            }

            // Calculate the new board ID based on existing boards
            int newBoardId = globals.boards.Any() ? globals.boards.Max(board => board.BoardId) + 1 : 1;

            // Create a new Board object
            Board newBoard = new Board
            {
                BoardId = newBoardId,
                Name = addBoardNameText.Text,
                Version = addBoardVersionText.Text,
                ComponentIds = globals.boardcomps.Select(comp => comp.ComponentId).ToList(), // Extract component IDs
                Quantities = globals.boardcomps.Select(comp => comp.Quantity).ToList(),     // Extract component quantities
                AmountMade = 0,    // Default value, can be set elsewhere if needed
                CanUsePNP = 0      // Default value, can be set based on other conditions if needed
            };

            newBoard.AmountMade = int.Parse(addBoardQuantityText.Text);
            if (pnpCompatibleCheck.Checked) newBoard.CanUsePNP = 1;

            // Add the new board to the global boards list
            globals.boards.Add(newBoard);

            globals.insertBoard(globals.boards[globals.boards.Count - 1]);

            // Show a success message
            MessageBox.Show("Board added successfully!", "Success", MessageBoxButtons.OK, MessageBoxIcon.Information);

            // Optionally clear the input fields for a fresh start
            addBoardIDText.Clear();
            addBoardNameText.Clear();
            addBoardVersionText.Clear();
            addBoardQuantityText.Clear();
            globals.boardcomps.Clear(); // Clear components list for the next board

            boardCompsViewer.DataSource = null;
            boardListView.DataSource = null;
            boardListView.DataSource = globals.boards;


            addBoardIDText.Text = (globals.boards.Count + 1).ToString();

        }

        private void addComponentToBoardButton_Click(object sender, EventArgs e)
        {
            // Check if required fields are filled
            if (string.IsNullOrWhiteSpace(addBoardComponentBox.Text) || string.IsNullOrWhiteSpace(addBoardCompQuantityBox.Text))
            {
                MessageBox.Show("Please fill in both the Component ID and Quantity fields.", "Missing Information", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return; // Exit the function if validation fails
            }

            // Check if the values are valid integers and greater than zero
            if (!int.TryParse(addBoardComponentBox.Text, out int componentId) || componentId <= 0 ||
                !int.TryParse(addBoardCompQuantityBox.Text, out int quantity) || quantity <= 0)
            {
                MessageBox.Show("Please enter valid numbers greater than zero for both Component ID and Quantity.", "Invalid Input", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return; // Exit the function if numeric validation fails
            }

            // Check if the component ID exists in globals.elComps
            var matchingComponent = globals.elComps.FirstOrDefault(comp => comp.ComponentId == componentId);
            if (matchingComponent == null)
            {
                MessageBox.Show("The specified Component ID does not exist in the database.", "Invalid Component ID", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return; // Exit the function if the component does not exist
            }

            // Add the new component to the board component list
            BoardComp newBoardComp = new BoardComp
            {
                ComponentId = componentId,
                Quantity = quantity
            };

            globals.boardcomps.Add(newBoardComp); // Add the BoardComp to the global list

            // Create a list of BoardCompViewModel for display with additional component details
            var displayList = globals.boardcomps.Select(boardComp =>
            {
                var component = globals.elComps.FirstOrDefault(elComp => elComp.ComponentId == boardComp.ComponentId);
                return new BoardCompViewModel
                {
                    ComponentId = boardComp.ComponentId,
                    Quantity = boardComp.Quantity,
                    ProductType = component?.ProductType ?? "N/A",
                    Package = component?.Package ?? "N/A",
                    Value = component?.Value ?? "N/A"
                };
            }).ToList();

            // Update the DataSource of boardCompsViewer to display the updated list with additional details
            boardCompsViewer.DataSource = null;  // Clear previous data binding
            boardCompsViewer.DataSource = displayList;  // Set new data binding with BoardCompViewModel list

            // Optionally clear the input fields for the next entry
            addBoardComponentBox.Clear();
            addBoardCompQuantityBox.Clear();
        }

        private void selectFromInventoryButton_Click(object sender, EventArgs e)
        {
            // Set the checkbox to true to indicate selection for a new board
            addToBoardCompsCheck.Checked = true;

            // Switch to the inventoryPage tab
            tabControl1.SelectTab("inventoryPage");
        }

        private void viewerDataGrid_CellClick(object sender, DataGridViewCellEventArgs e)
        {
            // Check if a valid row is selected and if we are in "add to board" mode
            if (e.RowIndex >= 0 && addToBoardCompsCheck.Checked)
            {
                // Get the selected component ID from the first cell of the selected row
                int selectedComponentId = Convert.ToInt32(viewerDataGrid.Rows[e.RowIndex].Cells["ComponentId"].Value);

                // Fill the ID field on mainPage with the selected component's ID
                addBoardComponentBox.Text = selectedComponentId.ToString();

                // Deselect the checkbox before jumping back
                addToBoardCompsCheck.Checked = false;

                // Clear search fields
                typeTextBox.Text = "";
                IDsearchTextBox.Text = "";
                valueTextBox.Text = "";
                supplierTextBox.Text = "";
                producerTextBox.Text = "";
                packageTextBox.Text = "";

                // Switch back to the mainPage tab
                tabControl1.SelectTab("mainPage");
            }
        }

        private void orderViewer_CellClick(object sender, DataGridViewCellEventArgs e)
        {
            if (orderViewer.SelectedRows.Count == 1 && globals.orderComponents.Count == 0) // Ensure exactly one row is selected
            {

                DataGridViewRow selectedRow = orderViewer.SelectedRows[0]; // Get the first (and only) selected row

                int orderId = Convert.ToInt32(selectedRow.Cells["OrderId"].Value); // Replace "OrderId" with the actual column name or index

                if (orderId <= globals.orders.Count)
                {

                    functions.ExtractOrderComponents(orderId, globals.selOrderComps, globals.orders, globals.elComps);

                    orderComponentsViewer.DataSource = null;
                    orderComponentsViewer.DataSource = globals.selOrderComps;

                }
            }
        }

        private void boardListView_CellClick(object sender, DataGridViewCellEventArgs e)
        {
            if (boardListView.SelectedRows.Count == 1) // Ensure exactly one row is selected
            {
                DataGridViewRow selectedRow = boardListView.SelectedRows[0]; // Get the selected row

                int boardId = Convert.ToInt32(selectedRow.Cells["BoardId"].Value); // Replace "BoardId" with the actual column name or index

                // Find the selected board in globals.boards
                var selectedBoard = globals.boards.FirstOrDefault(board => board.BoardId == boardId);
                if (selectedBoard == null)
                {
                    MessageBox.Show("Selected board not found.", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    return; // Exit if the board is not found
                }

                // Create a list of BoardCompViewModel for display in boardComponentsView
                var displayList = selectedBoard.ComponentIds.Select((componentId, index) =>
                {
                    var component = globals.elComps.FirstOrDefault(elComp => elComp.ComponentId == componentId);
                    return new BoardCompViewModel
                    {
                        ComponentId = componentId,
                        Quantity = selectedBoard.Quantities[index],
                        ProductType = component?.ProductType ?? "N/A",
                        Package = component?.Package ?? "N/A",
                        Value = component?.Value ?? "N/A"
                    };
                }).ToList();

                // Update the DataSource of boardComponentsView to show the components of the selected board
                boardComponentsView.DataSource = null;  // Clear previous data binding
                boardComponentsView.DataSource = displayList;  // Set new data binding with BoardCompViewModel list

            }
        }

        private void importBOMButton_Click(object sender, EventArgs e)
        {
            string filePath = "";
            openBoardBOM.ShowDialog(this);
            filePath = openBoardBOM.FileName;

            if (string.IsNullOrEmpty(filePath))
            {
                MessageBox.Show("No file selected.", "File Error", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            int missingComponentsCount = 0;
            List<string> unmatchedComponentsWithValues = new List<string>();  // Collect unmatched components with values

            try
            {
                using (var reader = new StreamReader(filePath))
                {
                    // Manually read the first line to skip the header row
                    reader.ReadLine();

                    using (var csv = new CsvReader(reader, new CsvConfiguration(CultureInfo.InvariantCulture)
                    {
                        HasHeaderRecord = false, // We've already skipped the header manually
                        Delimiter = "\t",         // Set this to the actual delimiter in your file (e.g., ";" or "\t" for tab)
                        BadDataFound = null      // Ignore bad data
                    }))
                    {
                        // Map by column index, assuming Quantity is first and Supplier Code is second
                        csv.Context.RegisterClassMap<BOMMapWithoutHeader>();

                        var bomComponents = csv.GetRecords<BOMComponent>().ToList();

                        globals.boardcomps.Clear();

                        foreach (var bomComp in bomComponents)
                        {
                            if (string.IsNullOrWhiteSpace(bomComp.SupplierPart))
                            {
                                missingComponentsCount++;
                                continue;
                            }

                            var matchingComponent = globals.elComps.FirstOrDefault(comp => comp.SellerCode == bomComp.SupplierPart);

                            if (matchingComponent != null)
                            {
                                BoardComp newBoardComp = new BoardComp
                                {
                                    ComponentId = matchingComponent.ComponentId,
                                    Quantity = bomComp.Quantity
                                };

                                globals.boardcomps.Add(newBoardComp);
                            }
                            else
                            {
                                // If no match found, check if there is a value, and add it to the unmatched list
                                if (!string.IsNullOrWhiteSpace(bomComp.SupplierPart))
                                {
                                    unmatchedComponentsWithValues.Add($"{bomComp.SupplierPart} (Qty: {bomComp.Quantity})");
                                }
                                missingComponentsCount++;
                            }
                        }
                    }
                }

                var displayList = globals.boardcomps.Select(boardComp =>
                {
                    var component = globals.elComps.FirstOrDefault(elComp => elComp.ComponentId == boardComp.ComponentId);
                    return new BoardCompViewModel
                    {
                        ComponentId = boardComp.ComponentId,
                        Quantity = boardComp.Quantity,
                        ProductType = component?.ProductType ?? "N/A",
                        Package = component?.Package ?? "N/A",
                        Value = component?.Value ?? "N/A"
                    };
                }).ToList();

                boardCompsViewer.DataSource = null;
                boardCompsViewer.DataSource = displayList;
                boardCompsViewer.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.AllCells;

                // Display a message if there are missing components
                if (missingComponentsCount > 0)
                {
                    string message = $"{missingComponentsCount} components in the BOM had no matching part in the inventory.";
                    if (unmatchedComponentsWithValues.Any())
                    {
                        message += "\n\nUnmatched components with specified values:\n" + string.Join("\n", unmatchedComponentsWithValues);
                    }
                    MessageBox.Show(message, "Missing Components", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                }

                // Set the board ID and navigate to the main page
                addBoardIDText.Text = (globals.boards.Count + 1).ToString();
                tabControl1.SelectTab("mainPage");

            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error reading BOM file: {ex.Message}", "File Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void addAmountButton_Click(object sender, EventArgs e)
        {
            UpdateComponentQuantity(isAdding: true);
        }

        private void reduceAmountButton_Click(object sender, EventArgs e)
        {
            UpdateComponentQuantity(isAdding: false);
        }

        private void UpdateComponentQuantity(bool isAdding)
        {
            // Ensure a component is selected in the DataGridView (replace 'elCompsViewer' with your DataGridView name)
            if (viewerDataGrid.SelectedRows.Count != 1)
            {
                MessageBox.Show("Please select a component to update.", "Selection Required", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            // Get the selected component ID
            DataGridViewRow selectedRow = viewerDataGrid.SelectedRows[0];
            int componentId = Convert.ToInt32(selectedRow.Cells["ComponentId"].Value);  // Replace "ComponentId" with the correct column name if different

            // Parse the quantity edit amount
            if (!int.TryParse(quantityEditAmount.Text, out int editAmount) || editAmount < 0)
            {
                MessageBox.Show("Please enter a valid, positive amount in the Quantity field.", "Invalid Input", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            // Find the component in globals.elComps
            var component = globals.elComps.FirstOrDefault(comp => comp.ComponentId == componentId);
            if (component == null)
            {
                MessageBox.Show("Selected component not found in inventory.", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return;
            }

            // Update the quantity
            if (isAdding)
            {
                component.QuantityLeft += editAmount;
            }
            else
            {
                component.QuantityLeft = Math.Max(0, component.QuantityLeft - editAmount);  // Prevent negative quantity
            }

            // Update the DataGridView to reflect the changes
            viewerDataGrid.Refresh();  // Refreshes the viewer to display the updated quantity

            // Call the DB update function
            globals.UpdateComponentInDB(component);

            // Clear the edit amount textbox for convenience
            quantityEditAmount.Clear();
        }

        private void typeTextBox_TextChanged(object sender, EventArgs e)
        {

            ApplyFilters();
                                    
        }

        private void valueTextBox_TextChanged(object sender, EventArgs e)
        {

            ApplyFilters();

        }

        private void IDsearchTextBox_TextChanged(object sender, EventArgs e)
        {

            ApplyFilters();

        }

        private void supplierTextBox_TextChanged(object sender, EventArgs e)
        {

            ApplyFilters();

        }

        private void producerTextBox_TextChanged(object sender, EventArgs e)
        {

            ApplyFilters();

        }

        private void packageTextBox_TextChanged(object sender, EventArgs e)
        {

            ApplyFilters();

        }

        private void jobInsertButton_Click(object sender, EventArgs e)
        {
            // Perform validation on required fields
            if (jobBoardCombo.SelectedIndex == -1 || string.IsNullOrWhiteSpace(jobBoardAmountBox.Text) || jobStatusCombo.SelectedIndex == -1)
            {
                MessageBox.Show("Please fill in all required fields: Board, Quantity, and Status.", "Missing Information", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;  // Exit if validation fails
            }

            // Parse and validate numeric fields
            if (!int.TryParse(jobBoardAmountBox.Text, out int quantity) || quantity <= 0)
            {
                MessageBox.Show("Please enter a valid quantity greater than zero.", "Invalid Input", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;  // Exit if quantity validation fails
            }

            // Generate a new job ID based on the maximum ID in the current jobs list
            int newJobId = globals.jobs.Count > 0 ? globals.jobs.Max(j => j.JobId) + 1 : 1;

            // Gather input from the form
            int selectedBoardId = (int)((dynamic)jobBoardCombo.SelectedItem).Value;
            bool usePnp = usePnpForJobCheck.Checked;
            string status = jobStatusCombo.SelectedItem.ToString();
            DateTime dueDate = jobDueDatePicker.Value;

            // Create the new Job object
            Job newJob = new Job
            {
                JobId = newJobId,
                BoardId = selectedBoardId,
                Quantity = quantity,
                UsePnp = usePnp,
                Status = status,
                DueDate = dueDate
            };

            // Add the new job to the global list
            globals.jobs.Add(newJob);

            // Insert the new job into the database
            globals.insertJob(newJob);

            // Create a JobViewModel list to include board names for display
            var jobViewModelList = globals.jobs.Select(job => new JobViewModel
            {
                JobId = job.JobId,
                BoardName = globals.boards.FirstOrDefault(b => b.BoardId == job.BoardId)?.Name + " - V" + globals.boards.FirstOrDefault(b => b.BoardId == job.BoardId)?.Version,
                Quantity = job.Quantity,
                UsePnp = job.UsePnp,
                Status = job.Status,
                DueDate = job.DueDate
            }).ToList();

            // Refresh the jobViewer to show the updated list of jobs
            jobViewer.DataSource = null;  // Clear the existing data binding
            jobViewer.DataSource = jobViewModelList;  // Bind the updated JobViewModel list

            // Clear the form fields for the next entry
            jobIDBox.Text = (newJobId + 1).ToString();
            jobBoardCombo.SelectedIndex = -1;
            jobBoardAmountBox.Clear();
            jobDueDatePicker.Value = DateTime.Today;
            usePnpForJobCheck.Checked = false;
            jobStatusCombo.SelectedIndex = -1;

            MessageBox.Show("Job added successfully.", "Success", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }

        private void jobSearchButton_Click(object sender, EventArgs e)
        {
            // Check if a specific Job ID is entered for the search
            if (int.TryParse(jobIDBox.Text, out int jobId))
            {
                // Search for a specific job by Job ID
                var jobToDisplay = globals.jobs.FirstOrDefault(job => job.JobId == jobId);

                if (jobToDisplay != null)
                {
                    // Display job details in the form fields
                    jobIDBox.Text = jobToDisplay.JobId.ToString();
                    jobBoardCombo.SelectedItem = jobBoardCombo.Items.Cast<dynamic>()
                                                .FirstOrDefault(item => item.Value == jobToDisplay.BoardId);
                    jobBoardAmountBox.Text = jobToDisplay.Quantity.ToString();
                    usePnpForJobCheck.Checked = jobToDisplay.UsePnp;
                    jobStatusCombo.SelectedItem = jobToDisplay.Status;
                    jobDueDatePicker.Value = jobToDisplay.DueDate;

                    // Disable fields and adjust button states
                    jobInsertButton.Enabled = false;
                    jobUpdateButton.Enabled = true;
                    jobCancelButton.Enabled = true;
                    jobIDBox.ReadOnly = true;
                    jobBoardCombo.Enabled = false;
                }
                else
                {
                    MessageBox.Show("Job not found.", "Search Result", MessageBoxButtons.OK, MessageBoxIcon.Information);
                }
            }
            else
            {
                // If no Job ID is provided, search based on other criteria
                var filteredJobs = globals.jobs.Where(job =>
                    (jobBoardCombo.SelectedIndex == -1 || job.BoardId == (int)((dynamic)jobBoardCombo.SelectedItem).Value) &&
                    (jobStatusCombo.SelectedIndex == -1 || job.Status == jobStatusCombo.SelectedItem.ToString())
                ).ToList();

                if (filteredJobs.Count == 1)
                {
                    // Display the single matching job in the form fields
                    var jobToDisplay = filteredJobs[0];
                    jobIDBox.Text = jobToDisplay.JobId.ToString();
                    jobBoardCombo.SelectedItem = jobBoardCombo.Items.Cast<dynamic>()
                                                .FirstOrDefault(item => item.Value == jobToDisplay.BoardId);
                    jobBoardAmountBox.Text = jobToDisplay.Quantity.ToString();
                    usePnpForJobCheck.Checked = jobToDisplay.UsePnp;
                    jobStatusCombo.SelectedItem = jobToDisplay.Status;
                    jobDueDatePicker.Value = jobToDisplay.DueDate;

                    // Disable fields and adjust button states
                    jobInsertButton.Enabled = false;
                    jobUpdateButton.Enabled = true;
                    jobCancelButton.Enabled = true;
                    jobIDBox.ReadOnly = true;
                    jobBoardCombo.Enabled = false;
                }
                else if (filteredJobs.Count > 1)
                {
                    // Display multiple matching jobs in the jobViewer
                    var jobViewModelList = filteredJobs.Select(job => new JobViewModel
                    {
                        JobId = job.JobId,
                        BoardName = globals.boards.FirstOrDefault(b => b.BoardId == job.BoardId)?.Name + " - V" + globals.boards.FirstOrDefault(b => b.BoardId == job.BoardId)?.Version,
                        Quantity = job.Quantity,
                        UsePnp = job.UsePnp,
                        Status = job.Status,
                        DueDate = job.DueDate
                    }).ToList();

                    jobViewer.DataSource = null;
                    jobViewer.DataSource = jobViewModelList;

                    // Adjust button states
                    jobInsertButton.Enabled = false;
                    jobUpdateButton.Enabled = true;
                    jobCancelButton.Enabled = true;
                }
                else
                {
                    MessageBox.Show("No matching jobs found.", "Search Result", MessageBoxButtons.OK, MessageBoxIcon.Information);
                }
            }
        }

        private void jobCancelButton_Click(object sender, EventArgs e)
        {
            // Clear fields and reset buttons
            jobIDBox.Clear();
            jobBoardCombo.SelectedIndex = -1;
            jobBoardAmountBox.Clear();
            jobDueDatePicker.Value = DateTime.Today;
            usePnpForJobCheck.Checked = false;
            jobStatusCombo.SelectedIndex = -1;

            jobInsertButton.Enabled = true;
            jobUpdateButton.Enabled = false;
            jobIDBox.ReadOnly = false;
            jobBoardCombo.Enabled = true;
        }

        private void jobBoardCombo_SelectedIndexChanged(object sender, EventArgs e)
        {
            if (jobBoardCombo.SelectedIndex >= 0)
            {
                int selectedBoardId = (int)((dynamic)jobBoardCombo.SelectedItem).Value;
                var selectedBoard = globals.boards.FirstOrDefault(board => board.BoardId == selectedBoardId);

                if (selectedBoard != null)
                {
                    usePnpForJobCheck.Enabled = selectedBoard.CanUsePNP == 1;
                    if (!usePnpForJobCheck.Enabled)
                    {
                        usePnpForJobCheck.Checked = false;
                    }
                }
            }
        }

        private void jobViewer_CellClick(object sender, DataGridViewCellEventArgs e)
        {
            // Ensure the user has clicked a valid row (not the header row)
            if (e.RowIndex < 0 || e.RowIndex >= globals.jobs.Count)
                return;

            // Retrieve the selected job based on the row index
            var selectedJob = globals.jobs[e.RowIndex];

            // Populate the form fields with the selected job's data
            jobIDBox.Text = selectedJob.JobId.ToString();

            // Find the board name and version from the job's BoardId
            var board = globals.boards.FirstOrDefault(b => b.BoardId == selectedJob.BoardId);
            if (board != null)
            {
                string boardDisplayName = $"{board.Name} - V{board.Version}";
                jobBoardCombo.SelectedItem = jobBoardCombo.Items.Cast<dynamic>()
                                              .FirstOrDefault(item => item.Text == boardDisplayName);
            }
            jobBoardAmountBox.Text = selectedJob.Quantity.ToString();
            usePnpForJobCheck.Checked = selectedJob.UsePnp;
            jobStatusCombo.SelectedItem = selectedJob.Status;
            jobDueDatePicker.Value = selectedJob.DueDate;

            // Disable ID and Board fields, as they should not be edited after selection
            jobIDBox.ReadOnly = true;
            jobBoardCombo.Enabled = false;

            // Adjust button states: enable only Update and Cancel buttons
            jobInsertButton.Enabled = false;
            jobUpdateButton.Enabled = true;
            jobSearchButton.Enabled = false;
            jobCancelButton.Enabled = true;
        }

        private void jobUpdateButton_Click(object sender, EventArgs e)
        {
            // Validate required fields
            if (string.IsNullOrWhiteSpace(jobBoardAmountBox.Text) || jobStatusCombo.SelectedIndex == -1)
            {
                MessageBox.Show("Please fill in all required fields: Quantity and Status.", "Missing Information", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            // Validate quantity as a positive integer
            if (!int.TryParse(jobBoardAmountBox.Text, out int quantity) || quantity <= 0)
            {
                MessageBox.Show("Please enter a valid quantity greater than zero.", "Invalid Input", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            // Get the JobId from jobIDBox and find the job in globals.jobs
            if (!int.TryParse(jobIDBox.Text, out int jobId))
            {
                MessageBox.Show("Invalid Job ID.", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return;
            }

            var jobToUpdate = globals.jobs.FirstOrDefault(job => job.JobId == jobId);
            if (jobToUpdate == null)
            {
                MessageBox.Show("Job not found.", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return;
            }

            // Update the job properties based on the form values
            jobToUpdate.Quantity = quantity;
            jobToUpdate.UsePnp = usePnpForJobCheck.Checked;
            jobToUpdate.Status = jobStatusCombo.SelectedItem.ToString();
            jobToUpdate.DueDate = jobDueDatePicker.Value;

            // Update the job in the database
            globals.UpdateJobInDB(jobToUpdate);

            // Refresh the jobViewer to show updated job information with board names
            var jobViewModelList = globals.jobs.Select(job => new JobViewModel
            {
                JobId = job.JobId,
                BoardName = globals.boards.FirstOrDefault(b => b.BoardId == job.BoardId)?.Name + " - V" + globals.boards.FirstOrDefault(b => b.BoardId == job.BoardId)?.Version,
                Quantity = job.Quantity,
                UsePnp = job.UsePnp,
                Status = job.Status,
                DueDate = job.DueDate
            }).ToList();

            jobViewer.DataSource = null;
            jobViewer.DataSource = jobViewModelList;

            // Clear the form and reset button states
            jobIDBox.Clear();
            jobBoardCombo.SelectedIndex = -1;
            jobBoardAmountBox.Clear();
            jobDueDatePicker.Value = DateTime.Today;
            usePnpForJobCheck.Checked = false;
            jobStatusCombo.SelectedIndex = -1;

            jobIDBox.ReadOnly = false;
            jobBoardCombo.Enabled = true;
            jobInsertButton.Enabled = true;
            jobSearchButton.Enabled = true;
            jobUpdateButton.Enabled = false;
            jobCancelButton.Enabled = false;

            MessageBox.Show("Job updated successfully.", "Success", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }

        private void orderSearchButton_Click(object sender, EventArgs e)
        {
            List<Order> filteredOrders;

            // Check if an Order ID is specified
            if (int.TryParse(orderIDTextBox.Text, out int orderId))
            {
                // Filter by Order ID
                filteredOrders = globals.orders.Where(order => order.OrderId == orderId).ToList();
            }
            else
            {
                // Filter by date range if Order ID is not specified
                DateTime startDate = orderDatePicker.Value.Date;
                DateTime endDate = orderDatePickerEnd.Value.Date;

                // Ensure the end date is inclusive by adding one day
                endDate = endDate.AddDays(1).AddSeconds(-1);

                filteredOrders = globals.orders.Where(order => order.OrderDate >= startDate && order.OrderDate <= endDate).ToList();
            }

            // Refresh the viewer with the filtered orders
            orderViewer.DataSource = null;
            orderViewer.DataSource = filteredOrders;
        }

        private void orderSearchClearButton_Click(object sender, EventArgs e)
        {
            // Clear the search fields
            orderIDTextBox.Clear();
            orderDatePicker.Value = DateTime.Today;
            orderDatePickerEnd.Value = DateTime.Today;

            // Reset the viewer to show all orders
            orderViewer.DataSource = null;
            orderViewer.DataSource = globals.orders;
        }

        private void pnpGeneratePartButton_Click(object sender, EventArgs e)
        {
            // Check if the component ID and height are provided and valid
            if (!int.TryParse(pnpIDBox.Text, out int componentID) || string.IsNullOrWhiteSpace(pnpHeightBox.Text))
            {
                MessageBox.Show("Please enter a valid component ID and height.", "Missing Information", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            // Fetch the component details based on the ID
            var component = globals.elComps.FirstOrDefault(comp => comp.ComponentId == componentID);
            if (component == null)
            {
                MessageBox.Show("Component not found. Please enter a valid component ID.", "Invalid ID", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return;
            }

            // Use default height of 0.5 if pnpHeightBox is empty
            string height = string.IsNullOrWhiteSpace(pnpHeightBox.Text) ? "0.5" : pnpHeightBox.Text;

            // Generate part text based on the component details and specified height
            string partText = $"<part id=\"{component.ComponentId}\" name=\"{component.ProductType}_{component.Value}_{component.Package}\" " +
                              $"height-units=\"Millimeters\" height=\"{height}\" package-id=\"{component.SmdFootprint}\" " +
                              $"speed=\"1.0\" pick-retry-count=\"0\"/>";

            // Display the generated part text in the read-only textbox for copy-pasting
            pnpPartText.Text = partText;
        }

        private void pnpPartResetButton_Click(object sender, EventArgs e)
        {
            pnpIDBox.Text = "";
            pnpHeightBox.Text = "";
            pnpPartText.Text = "";
        }

        private void openKicadFileButton_Click(object sender, EventArgs e)
        {
            // Step 1: Validate input fields
            if (string.IsNullOrWhiteSpace(footprintWBox.Text) ||
                string.IsNullOrWhiteSpace(footprintHBox.Text) ||
                string.IsNullOrWhiteSpace(footprintIDBox.Text) ||
                string.IsNullOrWhiteSpace(footprintDescBox.Text))
            {
                MessageBox.Show("Please fill in all fields: Width, Height, Package ID, and Description.",
                                "Missing Information",
                                MessageBoxButtons.OK,
                                MessageBoxIcon.Warning);
                return; // Exit the function if validation fails
            }

            // Step 2: Check that width and height fields are valid numbers, using InvariantCulture
            if (!double.TryParse(footprintWBox.Text, NumberStyles.Float, CultureInfo.InvariantCulture, out double bodyWidth) ||
                !double.TryParse(footprintHBox.Text, NumberStyles.Float, CultureInfo.InvariantCulture, out double bodyHeight))
            {
                MessageBox.Show("Please enter valid numerical values for Width and Height.",
                                "Invalid Input",
                                MessageBoxButtons.OK,
                                MessageBoxIcon.Warning);
                return; // Exit the function if numerical validation fails
            }

            // Step 3: Open the file dialog to select the KiCad footprint file
            if (openKicadFile.ShowDialog() == DialogResult.OK)
            {
                string filePath = openKicadFile.FileName;
                string packageId = footprintIDBox.Text;
                string description = footprintDescBox.Text;

                // Step 4: Parse KiCad file and generate XML using the Functions class
                Functions functions = new Functions();
                try
                {
                    functions.ParseKiCadFile(filePath); // Parse the KiCad file to extract pad data

                    // Generate XML based on parsed data, body width, and body height
                    string xmlOutput = functions.GenerateOpenPnPXML(packageId, description, bodyWidth, bodyHeight);

                    // Step 5: Output the generated XML to the footprintOutputBox
                    footprintOutputBox.Text = xmlOutput;
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Error processing KiCad file: {ex.Message}", "File Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
            }
        }

        private void viewerDataGrid_CellContentClick(object sender, DataGridViewCellEventArgs e)
        {

        }
    }


    public class DBhandler
    {
        public string locationDB = "Data Source=" + "C:\\Users\\Mattia\\Documents\\GitHub\\StockManager\\ELEC.db";
        
        public ElComp readElCompDBbyID(int ID, SQLiteConnection connection)
        {
            ElComp fetched = new ElComp();

            var sending = connection.CreateCommand();
            sending.CommandText = @"SELECT component_id, seller_code, seller, manufacturer, manufacturer_code, smd_footprint, 
                            package, product_type, value, price, quantity_left
                            FROM Components WHERE component_id = @ID";

            // Use parameterized queries to prevent SQL injection
            sending.Parameters.AddWithValue("@ID", ID);

            try
            {
                using (var reader = sending.ExecuteReader())
                {
                    if (reader.Read()) // Check if there are any rows returned
                    {
                        fetched.ComponentId = reader.GetInt32(0);  // Assuming the order of the columns matches the SELECT statement
                        fetched.SellerCode = reader.GetString(1);  // seller_code
                        fetched.Seller = reader.GetString(2);      // seller
                        fetched.Manufacturer = reader.GetString(3); // manufacturer
                        fetched.ManufacturerCode = reader.GetString(4); // manufacturer_code
                        fetched.SmdFootprint = reader.GetString(5); // smd_footprint
                        fetched.Package = reader.GetString(6); // package
                        fetched.ProductType = reader.GetString(7); // product_type
                        fetched.Value = reader.IsDBNull(8) ? null : reader.GetString(8); // value (can be null)
                        fetched.Price = reader.GetDouble(9); // price
                        fetched.QuantityLeft = reader.GetInt32(10); // quantity_left
                    }
                    else Globals.isReadDone = true;
                }
            }
            catch (SQLiteException e)
            {
                Console.WriteLine(e.Message);
                Globals.isReadDone = true;
            }

            return fetched;
        }
        
        public Order readOrderByID(int ID, SQLiteConnection connection)
        {
            Order fetchedOrder = new Order();

            var sending = connection.CreateCommand();
            sending.CommandText = @"SELECT order_id, order_date, supplier, components, total_cost, status
                            FROM Orders WHERE order_id = @ID";

            // Use parameterized queries to prevent SQL injection
            sending.Parameters.AddWithValue("@ID", ID);

            try
            {
                using (var reader = sending.ExecuteReader())
                {
                    if (reader.Read()) // Check if there are any rows returned
                    {
                        // Fill the Order object with the data from the database
                        fetchedOrder.OrderId = reader.GetInt32(0);  // order_id
                        fetchedOrder.OrderDate = reader.GetDateTime(1);  // order_date
                        fetchedOrder.Supplier = reader.GetString(2);  // supplier

                        // Deserialize the JSON field for components
                        string componentsJson = reader.GetString(3);
                        var orderComponents = JsonSerializer.Deserialize<List<OrderComponent>>(componentsJson);

                        // Initialize the lists
                        fetchedOrder.ComponentIds = new List<int>();
                        fetchedOrder.Quantities = new List<int>();
                        fetchedOrder.Prices = new List<double>();

                        // Populate the component lists
                        foreach (var component in orderComponents)
                        {
                            fetchedOrder.ComponentIds.Add(component.ComponentId);
                            fetchedOrder.Quantities.Add(component.Quantity);
                            fetchedOrder.Prices.Add(Math.Round(component.Price, 3));
                        }

                        // Fill the rest of the fields
                        fetchedOrder.TotalCost = Math.Round(reader.GetDouble(4), 2);  // total_cost
                        fetchedOrder.Status = reader.GetString(5);  // status
                    }
                    else
                    {
                        Globals.isReadDone = true;  // No more records, stop reading
                    }
                }
            }
            catch (SQLiteException e)
            {
                Console.WriteLine(e.Message);
                Globals.isReadDone = true;
            }

            return fetchedOrder;
        }
        
        public Board readBoardByID(int boardID, SQLiteConnection connection)
        {
            Board fetchedBoard = new Board();

            var command = connection.CreateCommand();
            command.CommandText = @"SELECT board_id, name, version, components, comp_quantities, boards_made, can_use_pnp
                            FROM Boards WHERE board_id = @BoardID";
            command.Parameters.AddWithValue("@BoardID", boardID);

            try
            {
                using (var reader = command.ExecuteReader())
                {
                    if (reader.Read())
                    {
                        // Populate the Board object with data from the database
                        fetchedBoard.BoardId = reader.GetInt32(0);
                        fetchedBoard.Name = reader.GetString(1);
                        fetchedBoard.Version = reader.GetString(2);

                        // Deserialize the components and comp_quantities JSON fields
                        string componentsJson = reader.GetString(3);
                        fetchedBoard.ComponentIds = JsonSerializer.Deserialize<List<int>>(componentsJson);

                        string quantitiesJson = reader.GetString(4);
                        fetchedBoard.Quantities = JsonSerializer.Deserialize<List<int>>(quantitiesJson);

                        fetchedBoard.AmountMade = reader.GetInt32(5);
                        fetchedBoard.CanUsePNP = reader.GetInt32(6);
                    }
                    else
                    {
                        fetchedBoard.BoardId = 0;  // Set to 0 to indicate the board does not exist
                    }
                }
            }
            catch (SQLiteException e)
            {
                Console.WriteLine($"Error reading board by ID: {e.Message}");
            }

            return fetchedBoard;
         
        }

        public Job readJobByID(int jobID, SQLiteConnection connection)
        {
            Job fetchedJob = new Job();

            var command = connection.CreateCommand();
            command.CommandText = @"SELECT job_id, board_id, quantity, pnp_job, status, due_date
                            FROM Jobs WHERE job_id = @JobID";
            command.Parameters.AddWithValue("@JobID", jobID);

            try
            {
                using (var reader = command.ExecuteReader())
                {
                    if (reader.Read())
                    {
                        // Populate the Job object with data from the database
                        fetchedJob.JobId = reader.GetInt32(0);
                        fetchedJob.BoardId = reader.GetInt32(1);
                        fetchedJob.Quantity = reader.GetInt32(2);
                        fetchedJob.UsePnp = reader.GetInt32(3) == 1;
                        fetchedJob.Status = reader.GetString(4);
                        fetchedJob.DueDate = reader.GetDateTime(5);
                    }
                    else
                    {
                        fetchedJob.JobId = 0;  // Set to 0 to indicate the job does not exist
                    }
                }
            }
            catch (SQLiteException e)
            {
                Console.WriteLine($"Error reading job by ID: {e.Message}");
            }

            return fetchedJob;
        }

        public void InsertOrderInDB(Order order, List<OrderComponent> orderComponents, SQLiteConnection connection)
        {
            // Serialize the components, quantities, and prices into JSON format
            var componentsList = orderComponents;

            // Convert the list to JSON
            string componentsJson = JsonSerializer.Serialize(componentsList);

            // Prepare the SQL query to insert the order into the database
            var sending = connection.CreateCommand();
            sending.CommandText = @"INSERT INTO Orders (order_date, supplier, components, total_cost, status)
                                VALUES (@OrderDate, @Supplier, @Components, @TotalCost, @Status)";

            // Use parameterized queries to safely insert values
            sending.Parameters.AddWithValue("@OrderDate", order.OrderDate);
            sending.Parameters.AddWithValue("@Supplier", order.Supplier);
            sending.Parameters.AddWithValue("@Components", componentsJson);  // JSON for components
            sending.Parameters.AddWithValue("@TotalCost", order.TotalCost);
            sending.Parameters.AddWithValue("@Status", order.Status);

            try
            {
                sending.ExecuteNonQuery();  // Execute the SQL command to insert the order
                Console.WriteLine("Order inserted successfully.");
            }
            catch (SQLiteException e)
            {
                Console.WriteLine($"Error inserting order: {e.Message}");
            }
        }

        public void InsertComponentInDB(ElComp component, SQLiteConnection connection)
        {
            // Prepare the SQL query to insert the component into the database
            var command = connection.CreateCommand();
            command.CommandText = @"INSERT INTO Components (component_id, seller_code, seller, manufacturer, manufacturer_code, smd_footprint, package, product_type, value, price, quantity_left)
                            VALUES (@ComponentId, @SellerCode, @Seller, @Manufacturer, @ManufacturerCode, @SmdFootprint, @Package, @ProductType, @Value, @Price, @QuantityLeft)";

            // Use parameterized queries to safely insert values
            command.Parameters.AddWithValue("@ComponentId", component.ComponentId);
            command.Parameters.AddWithValue("@SellerCode", component.SellerCode);
            command.Parameters.AddWithValue("@Seller", component.Seller);
            command.Parameters.AddWithValue("@Manufacturer", component.Manufacturer);
            command.Parameters.AddWithValue("@ManufacturerCode", component.ManufacturerCode);
            command.Parameters.AddWithValue("@SmdFootprint", component.SmdFootprint);
            command.Parameters.AddWithValue("@Package", component.Package);
            command.Parameters.AddWithValue("@ProductType", component.ProductType);
            command.Parameters.AddWithValue("@Value", component.Value);
            command.Parameters.AddWithValue("@Price", component.Price);
            command.Parameters.AddWithValue("@QuantityLeft", component.QuantityLeft);

            try
            {
                command.ExecuteNonQuery();  // Execute the SQL command to insert the component
                Console.WriteLine("Component inserted successfully.");
            }
            catch (SQLiteException e)
            {
                Console.WriteLine($"Error inserting component: {e.Message}");
            }
        }

        public void InsertBoardInDB(Board board, List<BoardComp> boardComponents, SQLiteConnection connection)
        {

            // Prepare the SQL query to insert the board into the database
            var sending = connection.CreateCommand();
            sending.CommandText = @"INSERT INTO Boards (name, version, components, comp_quantities, boards_made, can_use_pnp)
                            VALUES (@Name, @Version, @Components, @CompQuantities, @BoardsMade, @CanUsePNP)";

            // Use parameterized queries to safely insert values
            sending.Parameters.AddWithValue("@Name", board.Name);
            sending.Parameters.AddWithValue("@Version", board.Version);
            sending.Parameters.AddWithValue("@Components", JsonSerializer.Serialize(board.ComponentIds)); // JSON for component IDs and quantities
            sending.Parameters.AddWithValue("@CompQuantities", JsonSerializer.Serialize(board.Quantities)); // Quantities JSON
            sending.Parameters.AddWithValue("@BoardsMade", board.AmountMade);
            sending.Parameters.AddWithValue("@CanUsePNP", board.CanUsePNP);

            try
            {
                sending.ExecuteNonQuery();  // Execute the SQL command to insert the board
                Console.WriteLine("Board inserted successfully.");
            }
            catch (SQLiteException e)
            {
                Console.WriteLine($"Error inserting board: {e.Message}");
            }
        }

        public void InsertJobInDB(Job job, SQLiteConnection connection)
        {
            // Prepare the SQL query to insert the job into the database
            var command = connection.CreateCommand();
            command.CommandText = @"INSERT INTO Jobs (board_id, quantity, pnp_job, status, due_date)
                            VALUES (@BoardId, @Quantity, @PnpJob, @Status, @DueDate)";

            // Use parameterized queries to safely insert values
            command.Parameters.AddWithValue("@BoardId", job.BoardId);
            command.Parameters.AddWithValue("@Quantity", job.Quantity);
            command.Parameters.AddWithValue("@PnpJob", job.UsePnp ? 1 : 0);  // Convert bool to 1/0 for the database
            command.Parameters.AddWithValue("@Status", job.Status);
            command.Parameters.AddWithValue("@DueDate", job.DueDate);

            try
            {
                command.ExecuteNonQuery();  // Execute the SQL command to insert the job
                Console.WriteLine("Job inserted successfully.");
            }
            catch (SQLiteException e)
            {
                Console.WriteLine($"Error inserting job: {e.Message}");
            }
        }

        public void UpdateFullComponentInDB(ElComp component, SQLiteConnection connection)
        {
            var command = connection.CreateCommand();
            command.CommandText = @"UPDATE Components 
                            SET seller_code = @SellerCode,
                                seller = @Seller,
                                manufacturer = @Manufacturer,
                                manufacturer_code = @ManufacturerCode,
                                smd_footprint = @SmdFootprint,
                                package = @Package,
                                product_type = @ProductType,
                                value = @Value,
                                price = @Price,
                                quantity_left = @QuantityLeft
                            WHERE component_id = @ComponentId";

            // Set parameters for the query
            command.Parameters.AddWithValue("@SellerCode", component.SellerCode);
            command.Parameters.AddWithValue("@Seller", component.Seller);
            command.Parameters.AddWithValue("@Manufacturer", component.Manufacturer);
            command.Parameters.AddWithValue("@ManufacturerCode", component.ManufacturerCode);
            command.Parameters.AddWithValue("@SmdFootprint", component.SmdFootprint);
            command.Parameters.AddWithValue("@Package", component.Package);
            command.Parameters.AddWithValue("@ProductType", component.ProductType);
            command.Parameters.AddWithValue("@Value", component.Value ?? (object)DBNull.Value); // Handle potential null values
            command.Parameters.AddWithValue("@Price", component.Price);
            command.Parameters.AddWithValue("@QuantityLeft", component.QuantityLeft);
            command.Parameters.AddWithValue("@ComponentId", component.ComponentId);

            try
            {
                command.ExecuteNonQuery();  // Execute the SQL command to update the component
                Console.WriteLine("Component updated successfully.");
            }
            catch (SQLiteException e)
            {
                Console.WriteLine($"Error updating component: {e.Message}");
            }
        }

        public void UpdateFullJobInDB(Job job, SQLiteConnection connection)
        {
            var command = connection.CreateCommand();
            command.CommandText = @"UPDATE Jobs 
                            SET board_id = @BoardId,
                                quantity = @Quantity,
                                pnp_job = @PnpJob,
                                status = @Status,
                                due_date = @DueDate
                            WHERE job_id = @JobId";

            // Set parameters for the query
            command.Parameters.AddWithValue("@BoardId", job.BoardId);
            command.Parameters.AddWithValue("@Quantity", job.Quantity);
            command.Parameters.AddWithValue("@PnpJob", job.UsePnp ? 1 : 0);  // Convert boolean to 1/0 for the database
            command.Parameters.AddWithValue("@Status", job.Status);
            command.Parameters.AddWithValue("@DueDate", job.DueDate);
            command.Parameters.AddWithValue("@JobId", job.JobId);

            try
            {
                command.ExecuteNonQuery();  // Execute the SQL command to update the job
                Console.WriteLine("Job updated successfully.");
            }
            catch (SQLiteException e)
            {
                Console.WriteLine($"Error updating job: {e.Message}");
            }
        }

    }

    public class Globals
    {

        public static bool isReadDone = false;
        public static string globalFilter = "";
        public static bool isCurrencyEuros = true;
        public static int prevOrderSelection = 0;
        public static string orderFilePath = "";
        public static LcscOrderItem currentLCSCMissingComponent;
        public static MouserOrderItem currentMouserMissingComponent;

        public List<ElComp> elComps = new List<ElComp> { };
        public List<ElComp> viewerElComps = new List<ElComp> { };
        public List<Order> orders = new List<Order> { };
        public List<Board> boards = new List<Board> { };
        public List<Job> jobs = new List<Job> { };
        public List<BoardComp> boardcomps = new List<BoardComp> { };
        public List<OrderComp> selOrderComps = new List<OrderComp> { };
        public List<OrderComponent> orderComponents = new List<OrderComponent> { };

        public Functions functions = new Functions();
        public DBhandler dbhandler = new DBhandler();

        public void readElComp()
        {

            var connection = new SQLiteConnection(dbhandler.locationDB);

            connection.Open();

            isReadDone = false;

            elComps = functions.readElComps(1, elComps, connection);

            connection.Close();

        }
        
        public void readOrders()
        {
            var connection = new SQLiteConnection(dbhandler.locationDB);  // Open the connection to the database

            connection.Open();  // Open the database connection

            isReadDone = false;  // Initialize the flag to indicate reading is in progress

            orders = functions.readOrders(1, orders, connection);  // Read orders starting from ID 1

            connection.Close();  // Close the database connection when done
        }

        public void readBoards()
        {
            var connection = new SQLiteConnection(dbhandler.locationDB);  // Open the connection to the database

            connection.Open();  // Open the database connection

            isReadDone = false;  // Initialize the flag to indicate reading is in progress

            boards = functions.readBoards(1, boards, connection);  // Start reading boards from ID 1

            connection.Close();  // Close the database connection when done
        }

        public void readJobs()
        {
            var connection = new SQLiteConnection(dbhandler.locationDB);  // Open the connection to the database

            connection.Open();  // Open the database connection

            isReadDone = false;  // Initialize the flag to indicate reading is in progress

            jobs = functions.readJobs(1, jobs, connection);  // Start reading jobs from ID 1

            connection.Close();  // Close the database connection when done
        }

        public void insertOrder(Order order)
        {
            var connection = new SQLiteConnection(dbhandler.locationDB);  // Open the connection to the database

            connection.Open();  // Open the database connection

            dbhandler.InsertOrderInDB(order, orderComponents , connection);

            connection.Close();  // Close the database connection when done

        }

        public void InsertComponent(ElComp component)
        {
            var connection = new SQLiteConnection(dbhandler.locationDB);  // Open the connection to the database

            connection.Open();  // Open the database connection

            dbhandler.InsertComponentInDB(component, connection);  // Insert the component

            connection.Close();  // Close the database connection when done
        }
        
        public void insertBoard(Board board)
        {
            var connection = new SQLiteConnection(dbhandler.locationDB);  // Open the connection to the database

            connection.Open();  // Open the database connection

            // Assuming `boardComponents` is a global list containing the components for the board
            dbhandler.InsertBoardInDB(board, boardcomps, connection);

            connection.Close();  // Close the database connection when done
        }

        public void insertJob(Job job)
        {
            var connection = new SQLiteConnection(dbhandler.locationDB);  // Open the connection to the database

            connection.Open();  // Open the database connection

            dbhandler.InsertJobInDB(job, connection);  // Insert the job into the database

            connection.Close();  // Close the database connection when done
        }

        public void UpdateComponentInDB(ElComp component)
        {
            var connection = new SQLiteConnection(dbhandler.locationDB);

            connection.Open();  // Open the database connection

            dbhandler.UpdateFullComponentInDB(component, connection);

            connection.Close();  // Close the database connection when done
        }

        public void UpdateJobInDB(Job job)
        {
            var connection = new SQLiteConnection(dbhandler.locationDB);  // Open the connection to the database

            connection.Open();  // Open the database connection

            dbhandler.UpdateFullJobInDB(job, connection);  // Call the DB handler function to update the job

            connection.Close();  // Close the database connection when done
        }

    }

    public class Functions
    {
        public List<Pad> Pads { get; private set; } = new List<Pad>();



        public List<ElComp> readElComps(int startID, List<ElComp> elComps, SQLiteConnection connection)
        {
            //scanning variable
            int currID = startID;

            while (!Globals.isReadDone)
            {
                //init handler
                DBhandler dBhandler = new DBhandler();
                ElComp resulting = dBhandler.readElCompDBbyID(currID, connection);

                if (resulting.ManufacturerCode != null)
                {
                    elComps.Add(resulting);

                    currID = currID + 1;
                }

            }

            return elComps;

        }

        public List<Order> readOrders(int startID, List<Order> orders, SQLiteConnection connection)
        {
            // Scanning variable
            int currID = startID;

            while (!Globals.isReadDone)
            {
                // Init handler
                DBhandler dBhandler = new DBhandler();

                // Fetch the order by its ID (assume readOrderByID is already implemented)
                Order resultingOrder = dBhandler.readOrderByID(currID, connection);

                // Assuming if OrderId is 0, the order does not exist
                if (resultingOrder.OrderId != 0)
                {
                    // Add the valid order to the list
                    orders.Add(resultingOrder);

                    // Move to the next ID
                    currID = currID + 1;
                }
            }

            return orders;
        }

        public List<Board> readBoards(int startID, List<Board> boards, SQLiteConnection connection)
        {
            int currID = startID;

            while (!Globals.isReadDone)
            {
                DBhandler dbHandler = new DBhandler();

                // Fetch the board by its ID
                Board resultingBoard = dbHandler.readBoardByID(currID, connection);

                // If BoardId is 0, the board does not exist, so stop reading
                if (resultingBoard.BoardId != 0)
                {
                    boards.Add(resultingBoard);  // Add the valid board to the list
                    currID++;  // Move to the next ID
                }
                else
                {
                    Globals.isReadDone = true;  // Stop if no board found for the current ID
                }
            }

            return boards;
        }

        public List<Job> readJobs(int startID, List<Job> jobs, SQLiteConnection connection)
        {
            int currID = startID;

            while (!Globals.isReadDone)
            {
                DBhandler dbHandler = new DBhandler();

                // Fetch the job by its ID
                Job resultingJob = dbHandler.readJobByID(currID, connection);

                // If JobId is 0, the job does not exist, so stop reading
                if (resultingJob.JobId != 0)
                {
                    jobs.Add(resultingJob);  // Add the valid job to the list
                    currID++;  // Move to the next ID
                }
                else
                {
                    Globals.isReadDone = true;  // Stop if no job found for the current ID
                }
            }

            return jobs;
        }

        public List<ElComp> filterElComps(List<ElComp> elComps)
        {
            //variables to handle filtering
            string filters = Globals.globalFilter;
            string valCandidate = "";
            bool consec = true;
            bool isFootprint = true;   //true if there is a space after the footprint. Assumed until differently proved

            //results list
            List<ElComp> filtered = new List<ElComp>();
            List<ElComp> elCompValued = new List<ElComp>();

            //search for the first number written
            foreach (char a in filters)
            {
                if (char.IsNumber(a) && consec == true)
                {
                    valCandidate += a;
                }
                else if (a == ' ' && valCandidate.Length > 0)
                {
                    consec = false;
                }
                else if (a == ' ' && valCandidate.Length > 2)
                {
                    isFootprint = true;
                }
                else if (!char.IsNumber(a) && valCandidate.Length > 0)
                {
                    consec = false;
                    isFootprint = false;
                    valCandidate += a;
                }
            }

            foreach (ElComp target in elComps)
            {
                if (valCandidate != "" && target.Value.Contains(valCandidate) && !isFootprint) elCompValued.Add(target);
                else if(valCandidate == "" || isFootprint) elCompValued.Add(target);
            }

            //match with the type
            if (filters.Contains("cap") || filters.Contains("cond"))
            {
                foreach (ElComp target in elCompValued)
                {
                    if (target.ProductType.ToLower().Contains("cap") && target.SmdFootprint.Contains(valCandidate))
                    {
                        filters = filters.Replace("cap", " ").Trim();
                        filters = filters.Replace("cond", " ").Trim();

                        if (!filters.Contains("u") && !filters.Contains("n") && !filters.Contains("p")) filtered.Add(target);
                        else if (filters.Contains("u") && target.Value.Contains("u")) filtered.Add(target);
                        else if (filters.Contains("n") && target.Value.Contains("n")) filtered.Add(target);
                        else if (filters.Contains("p") && target.Value.Contains("p")) filtered.Add(target);
                    }
                }
            }
            else if (filters.Contains("res"))
            {
                foreach (ElComp target in elCompValued)
                {
                    if (target.ProductType.ToLower().Contains("res") && target.SmdFootprint.Contains(valCandidate))
                    {
                        filters = filters.Replace("res", " ").Trim();
                        if (!filters.Contains("m") && !filters.Contains("meg") && !filters.Contains("r") && !filters.Contains("k")) filtered.Add(target);
                        else if (filters.Contains("meg") && target.Value.Contains("M")) filtered.Add(target);
                        else if (filters.Contains("m") && target.Value.Contains("m")) filtered.Add(target);
                        else if (filters.Contains("k") && target.Value.Contains("k")) filtered.Add(target);
                        else if (filters.Contains("r") && target.Value.ToLower().Contains("r")) filtered.Add(target);

                    }
                }
            }
            else if (filters.Contains("led"))
            {
                foreach (ElComp target in elCompValued)
                {
                    if (target.ProductType.ToLower().Contains("led") && target.SmdFootprint.Contains(valCandidate))
                    {
                        filters = filters.Replace("led", " ").Trim();
                        if (!filters.Contains("y") && !filters.Contains("w") && 
                            !filters.Contains("r") && !filters.Contains("g") &&
                            !filters.Contains("b"))
                        {
                            filtered.Add(target);
                        }
                        else if (filters.Contains("rgb") && target.ProductType.ToLower().Contains("rgb")) filtered.Add(target);
                        else if (filters.Contains("y") && !filters.Contains("rgb") && target.ProductType.ToLower().Contains("y")) filtered.Add(target);
                        else if (filters.Contains("g") && !filters.Contains("rgb") && target.ProductType.ToLower().Contains("g")) filtered.Add(target);
                        else if (filters.Contains("b") && !filters.Contains("rgb") && target.ProductType.ToLower().Contains("b")) filtered.Add(target);
                        else if (filters.Contains("r") && !filters.Contains("rgb") && target.ProductType.ToLower().Contains("r")) filtered.Add(target);
                        else if (filters.Contains("w") && !filters.Contains("rgb") && target.ProductType.ToLower().Contains("w")) filtered.Add(target);

                    }
                }
            }
            else if (isFootprint)
            {
                foreach (ElComp elComp in elComps)
                {
                    if(elComp.Package.Contains(valCandidate)) filtered.Add(elComp);
                }   
            }

            return filtered;
        }

        public List<ElComp> filterElComps(List<ElComp> elComps, int ID = 0, string manufCode = "", string sellerCode = "",
                                  string type = "", string value = "", string package = "")
        {
            var filtered = new List<ElComp>();

            foreach (ElComp el in elComps)
            {
                if (ID > 0 && el.ComponentId == ID)
                {
                    filtered.Add(el);
                }
                else
                {
                    if (el.ManufacturerCode.ToLower().Contains(manufCode) &&
                        el.SellerCode.ToLower().Contains(sellerCode) &&
                        el.ProductType.ToLower().Contains(type) &&
                        el.Value.ToLower().Contains(value) &&
                        el.Package.ToLower().Contains(package))
                    {
                        filtered.Add(el);
                    }
                }
            }

            return filtered;
        }


        public List<LcscOrderItem> ReadLcscOrderItems(string filePath)
        {
            using (var reader = new StreamReader(filePath))
            using (var csv = new CsvReader(reader, CultureInfo.InvariantCulture))
            {
                // Read the header first to check for the currency symbol
                csv.Read();  // Read the first row (header)
                csv.ReadHeader();  // Set up the header context

                // Check if the header contains '$' to set the currency flag
                if (csv.HeaderRecord.Any(header => header.Contains("$")))
                {
                    Globals.isCurrencyEuros = false;  // It's in USD
                }
                else
                {
                    Globals.isCurrencyEuros = true;  // Default to EUR
                }

                // Now read and map the records
                csv.Context.RegisterClassMap<LcscOrderItemMap>();
                return new List<LcscOrderItem>(csv.GetRecords<LcscOrderItem>());
            }
        }

        public List<MouserOrderItem> ReadMouserOrderItems(string filePath)
        {
            using (var reader = new StreamReader(filePath))
            using (var csv = new CsvReader(reader, CultureInfo.InvariantCulture))
            {
                csv.Context.RegisterClassMap<MouserOrderItemMap>();
                return new List<MouserOrderItem>(csv.GetRecords<MouserOrderItem>());
            }
        }

        public void ExtractOrderComponents(int orderId, List<OrderComp> selOrderComps, List<Order> orders, List<ElComp> elComps)
        {
            // Clear the selOrderComps list before populating it
            selOrderComps.Clear();

            // Find the matching order by OrderId
            Order selectedOrder = orders.FirstOrDefault(order => order.OrderId == orderId);

            if (selectedOrder != null)
            {
                // Iterate through the components in the order
                for (int i = 0; i < selectedOrder.ComponentIds.Count; i++)
                {
                    int componentId = selectedOrder.ComponentIds[i];
                    int quantity = selectedOrder.Quantities[i];
                    double unitPrice = selectedOrder.Prices[i];

                    // Find the matching component in the elComps list
                    ElComp matchingComponent = elComps.FirstOrDefault(comp => comp.ComponentId == componentId);

                    if (matchingComponent != null)
                    {
                        // Create a new OrderComp object
                        OrderComp orderComp = new OrderComp
                        {
                            ComponentID = componentId,
                            Quantity = quantity,
                            SellerCode = matchingComponent.SellerCode,  // Get the SellerCode from the matching ElComp
                            UnitPrice = Math.Round(unitPrice, 3),
                            TotalPrice = Math.Round((unitPrice * quantity),2)
                        };

                        // Add the orderComp to the selOrderComps list
                        selOrderComps.Add(orderComp);
                    }
                }
            }
        }

        public List<ElComp> updateQuantities(List<ElComp> elComps, List<Order> orders, List<Board> boards)
        {
            // Step 1: Create dictionaries to store accumulated quantities from orders and boards
            Dictionary<int, int> orderedQuantities = new Dictionary<int, int>();
            Dictionary<int, int> usedQuantities = new Dictionary<int, int>();

            // Step 2: Calculate total ordered quantities for each component based on all orders
            foreach (var order in orders)
            {
                for (int i = 0; i < order.ComponentIds.Count; i++)
                {
                    int componentId = order.ComponentIds[i];
                    int orderQuantity = order.Quantities[i];

                    if (orderedQuantities.ContainsKey(componentId))
                        orderedQuantities[componentId] += orderQuantity;
                    else
                        orderedQuantities[componentId] = orderQuantity;
                }
            }

            // Step 3: Calculate total used quantities for each component based on all boards
            foreach (var board in boards)
            {
                for (int i = 0; i < board.ComponentIds.Count; i++)
                {
                    int componentId = board.ComponentIds[i];
                    int componentQuantityPerBoard = board.Quantities[i];
                    int totalUsedForBoard = componentQuantityPerBoard * board.AmountMade;

                    if (usedQuantities.ContainsKey(componentId))
                        usedQuantities[componentId] += totalUsedForBoard;
                    else
                        usedQuantities[componentId] = totalUsedForBoard;
                }
            }

            // Step 4: Update each component in elComps with the final quantity
            foreach (var component in elComps)
            {
                int componentId = component.ComponentId;

                // Get the total ordered and used quantities for this component
                int totalOrdered = orderedQuantities.ContainsKey(componentId) ? orderedQuantities[componentId] : 0;
                int totalUsed = usedQuantities.ContainsKey(componentId) ? usedQuantities[componentId] : 0;

                // Calculate final quantity: Amount = Amount_ordered - Amount_used
                component.QuantityLeft = totalOrdered - totalUsed;
            }

            return elComps;
        }

        public void ParseKiCadFile(string filePath)
        {
            Pads.Clear(); // Clear any previous pad data

            // Regex pattern with flexible spaces around elements
            var padPattern = @"\(\s*pad\s+(\d+)\s+smd\s+\w+\s+\(at\s+([-+]?[0-9]*\.?[0-9]+)\s+([-+]?[0-9]*\.?[0-9]+)\s*([-+]?[0-9]*\.?[0-9]*)?\)\s+\(size\s+([-+]?[0-9]*\.?[0-9]+)\s+([-+]?[0-9]*\.?[0-9]+)\)\s*(\(roundrect_rratio\s+([-+]?[0-9]*\.?[0-9]+)\))?";

            foreach (var line in File.ReadLines(filePath))
            {
                var match = Regex.Match(line, padPattern);

                if (match.Success)
                {
                    try
                    {
                        var pad = new Pad();

                        // Trim and validate the pad name
                        pad.Name = match.Groups[1].Value.Trim();

                        if (string.IsNullOrEmpty(pad.Name))
                        {
                            Console.WriteLine($"Skipping pad with empty or invalid name on line: {line}");
                            return;  // Skip adding this pad if the name is invalid
                        }

                        // Parse X and Y coordinates
                        pad.X = double.Parse(match.Groups[2].Value, CultureInfo.InvariantCulture);
                        pad.Y = double.Parse(match.Groups[3].Value, CultureInfo.InvariantCulture);

                        // Only parse Rotation if it's not an empty string
                        if (match.Groups[4].Success && !string.IsNullOrEmpty(match.Groups[4].Value))
                        {
                            pad.Rotation = double.Parse(match.Groups[4].Value, CultureInfo.InvariantCulture);
                        }
                        else
                        {
                            pad.Rotation = 0.0;  // Default to 0.0 if Rotation is missing
                        }

                        // Parse Width and Height
                        pad.Width = double.Parse(match.Groups[5].Value, CultureInfo.InvariantCulture);
                        pad.Height = double.Parse(match.Groups[6].Value, CultureInfo.InvariantCulture);

                        // Handle optional RoundRectRatio
                        if (match.Groups[7].Success && !string.IsNullOrEmpty(match.Groups[7].Value))
                        {
                            pad.RoundRectRatio = double.Parse(match.Groups[7].Value, CultureInfo.InvariantCulture);
                        }
                        else
                        {
                            pad.RoundRectRatio = 0.0;  // Default if not present
                        }

                        // Add the pad to the list if all parsing is successful
                        Pads.Add(pad);
                    }
                    catch (FormatException ex)
                    {
                        Console.WriteLine($"Error parsing pad data on line: {line}");
                        Console.WriteLine($"Exception message: {ex.Message}");
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"Unexpected error on line: {line}");
                        Console.WriteLine($"Exception message: {ex.Message}");
                    }
                }
                else
                {
                    Console.WriteLine($"No valid pad match found on line: {line}");
                }

            }

            if (Pads.Count == 0)
            {
                throw new InvalidOperationException("No valid pad data found in the KiCad file. Please check the file format.");
            }
        }

        public string GenerateOpenPnPXML(string packageId, string description, double bodyWidth, double bodyHeight)
        {
            if (Pads.Count == 0)
            {
                throw new InvalidOperationException("No pad data found. Please parse a KiCad file first.");
            }

            var xml = $"<package version=\"1.1\" id=\"{packageId}\" description=\"{description}\" pick-vacuum-level=\"0.0\" place-blow-off-level=\"0.0\">\n";
            xml += $"   <footprint units=\"Millimeters\" body-width=\"{bodyWidth.ToString(CultureInfo.InvariantCulture)}\" body-height=\"{bodyHeight.ToString(CultureInfo.InvariantCulture)}\">\n";

            foreach (var pad in Pads)
            {
                // Skip pads without valid names to avoid empty name errors in XML
                if (string.IsNullOrWhiteSpace(pad.Name))
                {
                    Console.WriteLine("Skipping pad with empty or invalid name.");
                    continue;
                }

                // Generate the XML for each pad, ensuring no additional quotes around the name
                xml += $"      <pad name=\"{pad.Name}\" x=\"{pad.X.ToString(CultureInfo.InvariantCulture)}\" y=\"{pad.Y.ToString(CultureInfo.InvariantCulture)}\" width=\"{pad.Width.ToString(CultureInfo.InvariantCulture)}\" height=\"{pad.Height.ToString(CultureInfo.InvariantCulture)}\" rotation=\"{pad.Rotation.ToString(CultureInfo.InvariantCulture)}\" roundness=\"{pad.RoundRectRatio.ToString(CultureInfo.InvariantCulture)}\" />\n";
            }

            xml += "   </footprint>\n</package>";
            return xml;
        }


    }

    public class ElComp
    {
        public int ComponentId { get; set; }             // Unique identifier (component_id)
        public string SellerCode { get; set; }           // Code from the seller (seller_code)
        public string Seller { get; set; }               // Seller name
        public string Manufacturer { get; set; }         // Manufacturer name
        public string ManufacturerCode { get; set; }     // Manufacturer code
        public string SmdFootprint { get; set; }         // SMD footprint
        public string Package { get; set; }              // Package type
        public string ProductType { get; set; }          // Type of product (resistor, capacitor, etc.)
        public string Value { get; set; }                // Component value (e.g., 1k for resistors, 100n for capacitors)
        public double Price { get; set; }               // Price of the last purchase
        public int QuantityLeft { get; set; }            // Number of components left in stock
    }

    public class OrderComp
    {
        public int ComponentID { get; set; }
        public int Quantity { get; set; }
        public string SellerCode { get; set; }
        public double UnitPrice { get; set; }
        public double TotalPrice { get; set; }

    }

    public class OrderComponent
    {
        public int ComponentId { get; set; }  // The ID of the component
        public int Quantity { get; set; }     // The quantity ordered
        public double Price { get; set; }     // The price of the component
    }

    public class Order
    {
        public int OrderId { get; set; }                  // Unique identifier for the order
        public DateTime OrderDate { get; set; }           // Date the order was placed
        public string Supplier { get; set; }              // Supplier name
        public List<int> ComponentIds { get; set; }       // List of component IDs in the order
        public List<int> Quantities { get; set; }         // List of quantities corresponding to each component
        public List<double> Prices { get; set; }         // List of prices for each component in the order
        public double TotalCost { get; set; }            // Total cost of the order
        public string Status { get; set; }                // Status of the order (e.g., "Pending", "Completed")
    }

    public class Board
    {
        public int BoardId { get; set; }                  // Unique identifier for the board
        public string Name { get; set; }                  // Name of the board design
        public string Version { get; set; }               // Version number of the board design
        public List<int> ComponentIds { get; set; }       // List of component IDs used in the board
        public List<int> Quantities { get; set; }         // List of quantities corresponding to each component
        public int AmountMade { get; set; }
        public int CanUsePNP { get; set; }

    }

    public class Job
    {
        public int JobId { get; set; }              // Unique identifier for the job
        public int BoardId { get; set; }            // ID of the board being produced (foreign key)
        public int Quantity { get; set; }           // Quantity of units to produce
        public bool UsePnp { get; set; }            // Whether the job requires PnP
        public string Status { get; set; }          // Status of the job
        public DateTime DueDate { get; set; }       // Due date for the job
    }

    public class Pad
    {
        public string Name { get; set; }
        public double X { get; set; }
        public double Y { get; set; }
        public double Width { get; set; }
        public double Height { get; set; }
        public double Rotation { get; set; }
        public double RoundRectRatio { get; set; }
    }

    public class LcscOrderItem
    {
        public string LcscPartNumber { get; set; }  // LCSC Part Number
        public string ManufacturerPartNumber { get; set; }  // Manufacturer Part Number
        public string Manufacturer { get; set; }  // Manufacturer Name
        public string Package { get; set; }  // Package Type
        public int OrderQuantity { get; set; }  // Quantity Ordered
        public double UnitPrice { get; set; }  // Unit Price in €
        public double OrderPrice { get; set; }  // Total Price in €
    }
    
    public class LcscOrderItemMap : ClassMap<LcscOrderItem>
    {
        public LcscOrderItemMap()
        {
            Map(m => m.LcscPartNumber).Name("LCSC Part Number");
            Map(m => m.ManufacturerPartNumber).Name("Manufacture Part Number");
            Map(m => m.Manufacturer).Name("Manufacturer");
            Map(m => m.Package).Name("Package");
            Map(m => m.OrderQuantity).Name("Order Qty.");
            Map(m => m.UnitPrice).Name("Unit Price(€)");
            //Map(m => m.UnitPrice).Name("Unit Price($)");
            Map(m => m.OrderPrice).Name("Order Price(€)");
            //Map(m => m.OrderPrice).Name("Order Price($)");
        }
    }

    public class MouserOrderItem
    {
        public string MouserPartNumber { get; set; }        // Mouser-specific part number
        public string ManufacturerPartNumber { get; set; }  // Manufacturer part number
        public int OrderQuantity { get; set; }              // Quantity ordered
        public double UnitPrice { get; set; }               // Price per unit
        public string Manufacturer { get; set; }            // Manufacturer name
    }

    public class MouserOrderItemMap : ClassMap<MouserOrderItem>
    {
        public MouserOrderItemMap()
        {
            Map(m => m.MouserPartNumber).Name("MouserPartNumber");
            Map(m => m.ManufacturerPartNumber).Name("ManufacturerPartNumber");
            Map(m => m.OrderQuantity).Name("OrderQuantity");
            Map(m => m.UnitPrice).Name("Price").TypeConverter<CurrencyConverter>();  // Apply the custom converter
            Map(m => m.Manufacturer).Name("Manufacturer");
        }
    }

    public class BoardComp
    {
        public int ComponentId { get; set; }  // Unique identifier for the component
        public int Quantity { get; set; }     // Quantity of this component used in the board
    }

    public class BoardCompViewModel
    {
        public int ComponentId { get; set; }
        public int Quantity { get; set; }
        public string ProductType { get; set; }
        public string Package { get; set; }
        public string Value { get; set; }
    }

    public class JobViewModel
    {
        public int JobId { get; set; }
        public string BoardName { get; set; }       // Combined board name and version
        public int Quantity { get; set; }
        public bool UsePnp { get; set; }
        public string Status { get; set; }
        public DateTime DueDate { get; set; }
    }

    public class BOMComponent
    {
        public int Quantity { get; set; }
        public string SupplierPart { get; set; }
    }

    public class BOMMapWithoutHeader : ClassMap<BOMComponent>
    {
        public BOMMapWithoutHeader()
        {
            Map(m => m.Quantity).Index(0);       // Map Quantity to the first column
            Map(m => m.SupplierPart).Index(1);   // Map Supplier Code to the second column
        }
    }

    public class CurrencyConverter : CsvHelper.TypeConversion.DoubleConverter
    {
        public override object ConvertFromString(string text, IReaderRow row, MemberMapData memberMapData)
        {
            if (string.IsNullOrWhiteSpace(text))
                return 0.0;

            // Remove any non-numeric characters except for commas, periods, and minus signs
            string numericString = Regex.Replace(text, @"[^\d,.-]", "");

            // Check if it contains a comma as the decimal separator
            if (numericString.Contains(",") && !numericString.Contains("."))
            {
                // Replace comma with period to standardize as a decimal point
                numericString = numericString.Replace(",", ".");
            }

            // Parse the cleaned string as a double using InvariantCulture
            if (double.TryParse(numericString, NumberStyles.Any, CultureInfo.InvariantCulture, out double result))
            {
                return result;
            }

            // Default to 0.0 if parsing fails
            return 0.0;
        }
    }

}
