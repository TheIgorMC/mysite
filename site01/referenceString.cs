using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace StringVisualizer
{    

    public partial class Form1 : Form
    {
        public class Globals
        {

            public static int strands = 14;

            public static double lenght = 0.00;

            public static int colorMode = 0; //0 normal, 1 double, 2 triple, 3 pinstripe, 4 triple w/ pinstripe, 5 single w/ pinstripe

            public static int discount = 0; //0 normal, -1 society, -2 friends

            public static int selCol1 = 0;
            public static int selCol2 = 0;
            public static int selCol3 = 0;
            public static int selCol4 = 0;

            // Array of color names
            public static string[] colorNames = new string[]
            {
    "White", "Root Beer", "Gold", "Cedar", "Black Cherry", "Medium Brown/Tan",
    "Pink", "Buckskin", "Flame", "Electric Red", "Light Blue", "Light Pink",
    "Green", "Dark Brown", "Purple", "Black", "Gunmetal", "Red", "Royal Blue",
    "Mountain Berry", "Sunset Orange", "Kiwi", "Natural", "Metallic Bronze",
    "OD Green", "Electric Blue", "Teal", "Yellow", "Silver", "Fluorescent Yellow",
    "Fluorescent Orange", "Fluorescent Green", "Fluorescent Purple", "Patriot",
    "Electric Blue & Black", "Royal Blue & Black", "Gold & Black", "Sunset Orange & Black",
    "Red & White", "Royal Blue & White", "Yellow & Black", "Black Cherry & Black",
    "Root Beer & Black", "Green & Black", "Pink & Black", "White & Black",
    "Tan & Black", "Silver & Black", "Red & Black", "Autumn", "Camo", "Winter Camo",
    "FLo. Green & Electric Blue", "Fluorescent Yellow & Black", "Fluorescent Orange & Black",
    "Fluorescent Green & Black", "Fluorescent Purple & Black"
            };

            // Array of primary color hex codes
            public static string[] primaryColors = new string[]
            {
    "#FFFFFF", "#753719", "#D4A017", "#C6873F", "#6F0E3A", "#A67B5B",
    "#FF69B4", "#CFA77B", "#FD3B00", "#FF0000", "#ADD8E6", "#FFB6C1",
    "#008000", "#654321", "#800080", "#000000", "#2A3439", "#FF0000", "#4169E1",
    "#8A2BE2", "#FD5E53", "#8EE53F", "#F5F5DC", "#6C541E", "#556B2F", "#7DF9FF",
    "#008080", "#FFFF00", "#C0C0C0", "#CCFF00", "#FF6700", "#00FF00", "#FF00FF",
    "#500000", "#7DF9FF", "#4169E1", "#D4A017", "#FD5E53", "#FF0000", "#4169E1",
    "#FFFF00", "#6F0E3A", "#753719", "#008000", "#FF69B4", "#FFFFFF", "#D2B48C",
    "#C0C0C0", "#FF0000", "#FF8C00", "#78866B", "#B0C4DE", "#00FF00", "#CCFF00",
    "#FF6700", "#00FF00", "#FF00FF"
            };

            // Array of secondary color hex codes
            public static string[] secondaryColors = new string[]
            {
    "#FFFFFF", "#753719", "#D4A017", "#C6873F", "#6F0E3A", "#A67B5B",
    "#FF69B4", "#CFA77B", "#FD3B00", "#FF0000", "#ADD8E6", "#FFB6C1",
    "#008000", "#654321", "#800080", "#000000", "#2A3439", "#FF0000", "#4169E1",
    "#8A2BE2", "#FD5E53", "#8EE53F", "#F5F5DC", "#6C541E", "#556B2F", "#7DF9FF",
    "#008080", "#FFFF00", "#C0C0C0", "#CCFF00", "#FF6700", "#00FF00", "#FF00FF",
    "#FFFFFF", "#000000", "#000000", "#000000", "#000000", "#FFFFFF", "#FFFFFF",
    "#000000", "#000000", "#000000", "#000000", "#000000", "#000000", "#000000",
    "#000000", "#000000", "#8B4513", "#3B3B3B", "#FFFFFF", "#7DF9FF", "#000000",
    "#000000", "#000000", "#000000"
            };

        }

        public class Functions
        {

            public static double updatePrice()
            {
                const double materialCostPerFootPerStrand = 4.63 / 87.33; // Euros per foot of string material per strand
                const double centerServingCostPerFoot = 0.27 / 2.89; // Euros per foot of center serving material
                const double endServingCostPerFoot = 0.27 / 2.89; // Euros per foot of end serving material
                const double laborCostPerHour = 10.00;
                const double laborTimePerString = 0.5; // 30 minutes per string

                const double centerServingLengthInches = 6; // Length of the center serving in inches
                const double endServingLengthInches = 2.5; // Length of each end serving in inches
                const double stringDiameterFor16Strands = 0.055; // Diameter of the string itself for 16 strands in inches


                // Convert length to feet
                double lengthFeet = Globals.lenght / 12.0;

                // Calculate material cost (considering the number of strands)
                double materialCost = lengthFeet * Globals.strands * materialCostPerFootPerStrand;

                // Calculate the string diameter based on strand count
                double stringDiameter = stringDiameterFor16Strands;

                // Calculate the length of serving material required (center serving)
                double centerServingCircumference = Math.PI * (stringDiameter + 2 * centerServingLengthInches / 12.0);
                double centerServingWraps = centerServingLengthInches / stringDiameter;
                double centerServingLengthFeet = (centerServingCircumference * centerServingWraps) / 12.0;
                double centerServingCost = centerServingLengthFeet * centerServingCostPerFoot;

                // Calculate the length of serving material required (end servings, two ends)
                double endServingCircumference = Math.PI * (stringDiameter + 2 * endServingLengthInches / 12.0);
                double endServingWraps = endServingLengthInches / stringDiameter;
                double endServingLengthFeet = ((endServingCircumference * endServingWraps) * 2) / 12.0; // Two ends
                double endServingCost = endServingLengthFeet * endServingCostPerFoot;

                // Calculate total serving cost
                double totalServingCost = centerServingCost + endServingCost;

                // Calculate labor cost
                double laborCost = laborCostPerHour * laborTimePerString;

                // Total cost
                double totalCostPerString;


                if (Globals.discount == -2) //amici
                {
                    totalCostPerString = materialCost + totalServingCost + (laborCost * 0.35);
                }
                else if (Globals.discount == -1) //club
                {
                    totalCostPerString = materialCost + totalServingCost + (laborCost * 0.15);
                }
                else
                {
                    double percent = (1.0 - (double.Parse(Globals.discount.ToString()) / 100.0));
                    totalCostPerString = (materialCost + totalServingCost + laborCost * 1.5) * percent;
                }

                // Extra charges for color combinations
                double extraCharge = 0.00;
                if (Globals.colorMode == 1) //double
                {
                    if (Globals.discount == -2) extraCharge = 1.00;
                    if (Globals.discount == -1) extraCharge = 0.50;
                    else extraCharge = 3.00;
                }
                else if (Globals.colorMode == 2) //triple
                {
                    if (Globals.discount == -2) extraCharge = 1.50;
                    if (Globals.discount == -1) extraCharge = 0.75;
                    else extraCharge = 4.00;
                }
                else if (Globals.colorMode == 3) //pinstripe
                {
                    if (Globals.discount == -2) extraCharge = 2.00;
                    if (Globals.discount == -1) extraCharge = 1.00;
                    else extraCharge = 5.00;
                }
                else if (Globals.colorMode == 4) //triple w/ pinstripe
                {
                    if (Globals.discount == -2) extraCharge = 3.00;
                    if (Globals.discount == -1) extraCharge = 1.50;
                    else extraCharge = 7.00;
                }
                else if (Globals.colorMode == 5) //single w/ pinstripe
                {
                    if (Globals.discount == -2) extraCharge = 1.00;
                    if (Globals.discount == -1) extraCharge = 0.50;
                    else extraCharge = 2.00;
                }

                return Math.Round((totalCostPerString + extraCharge), 1);
            }

            public static Bitmap drawbmp()
            {

                List<int> colors = new List<int>();

                switch (Globals.colorMode)
                {
                    case 0: //single
                        for(int i=0; i<Globals.strands; i++)
                        {
                            colors.Add(Globals.selCol1);
                        }
                        break;

                    case 1: //double
                        for (int i = 0; i < Globals.strands; i++)
                        {
                            if (i < Globals.strands / 2) colors.Add(Globals.selCol1);
                            else colors.Add(Globals.selCol2);
                        }
                        break;

                    case 2: //triple
                        for (int i = 0; i < Globals.strands; i++)
                        {
                            if (i < Globals.strands / 3) colors.Add(Globals.selCol1);
                            else if (i < (Globals.strands / 3)*2) colors.Add(Globals.selCol2);
                            else colors.Add(Globals.selCol3);
                        }
                        break;

                    case 3: //pinstripe
                        for (int i = 0; i < Globals.strands; i++)
                        {
                            if (i == 0 || i == Globals.strands / 2) colors.Add(Globals.selCol4);
                            else if (i < Globals.strands / 2) colors.Add(Globals.selCol1);
                            else colors.Add(Globals.selCol2);
                        }
                        break;

                    case 4: //triple w/ stripe
                        for (int i = 0; i < Globals.strands; i++)
                        {
                            if(i == Globals.strands - 1) colors.Add(Globals.selCol4);
                            else if (i < Globals.strands / 3) colors.Add(Globals.selCol1);
                            else if (i < (Globals.strands / 3) * 2) colors.Add(Globals.selCol2);
                            else colors.Add(Globals.selCol3);
                        }
                        break;

                    case 5: //single w/stripe
                        for (int i = 0; i < Globals.strands; i++)
                        {
                            if (i != 0) colors.Add(Globals.selCol1);
                            else colors.Add(Globals.selCol4);
                        }
                        break;
                }
                
                int w = 71;
                int h = 298;

                int y1 = 0;
                int y0 = -h-90;

                int off = 16;
                int lenght = off * Globals.strands;

                Bitmap bitmap = new Bitmap(w, h, System.Drawing.Imaging.PixelFormat.Format32bppPArgb);
                Graphics graphics = Graphics.FromImage(bitmap);

                for(int j=0; j<4; j++)
                {
                    for (int i = 0; i < Globals.strands; i++)
                    {
                        //coordinates
                        int xi = -30;
                        int yi = y0 + i * off + j * lenght;

                        int xf = w + 30;
                        int yf = y1 + i * off + j * lenght;

                        int a = 1 * i;
                        Pen pen = new Pen(ColorTranslator.FromHtml(Globals.primaryColors[colors[i]]), 6);

                        graphics.DrawLine(pen, xi, yi, xf, yf);
                    }
                }                
                               

                bitmap.Save("DrawBezierSpline.png");
                return bitmap;
            }

        }

        public Form1()
        {
            InitializeComponent();
        }

        private void colorDrop_SelectedIndexChanged(object sender, EventArgs e)
        {
            if (colorDrop.SelectedIndex == 0)
            {
                Globals.colorMode = 0;
                comboColor2.Visible = false;
                col2Label.Visible = false;
                comboColorTriple.Visible = false;
                col3Label.Visible = false;
                comboColorPinstripe.Visible = false;
                col4Label.Visible = false;
            }
            else if (colorDrop.SelectedIndex == 1)
            {
                Globals.colorMode = 1;
                comboColor2.Visible = true;
                col2Label.Visible = true;
                comboColorTriple.Visible = false;
                col3Label.Visible = false;
                comboColorPinstripe.Visible = false;
                col4Label.Visible = false;
            }
            else if (colorDrop.SelectedIndex == 2)
            {
                Globals.colorMode = 2;
                comboColor2.Visible = true;
                col2Label.Visible = true;
                comboColorTriple.Visible = true;
                col3Label.Visible = true;
                comboColorPinstripe.Visible = false;
                col4Label.Visible = false;
            }
            else if (colorDrop.SelectedIndex == 3)
            {
                Globals.colorMode = 3;
                comboColor2.Visible = true;
                col2Label.Visible = true;
                comboColorTriple.Visible = false;
                col3Label.Visible = false;
                comboColorPinstripe.Visible = true;
                col4Label.Visible = true;
            }
            else if (colorDrop.SelectedIndex == 4)
            {
                Globals.colorMode = 4;
                comboColor2.Visible = true;
                col2Label.Visible = true;
                comboColorTriple.Visible = true;
                col3Label.Visible = true;
                comboColorPinstripe.Visible = true;
                col4Label.Visible = true;
            }
            else if (colorDrop.SelectedIndex == 5)
            {
                Globals.colorMode = 5;
                comboColor2.Visible = false;
                col2Label.Visible = false;
                comboColorTriple.Visible = false;
                col3Label.Visible = false;
                comboColorPinstripe.Visible = true;
                col4Label.Visible = true;
            }

            previewBox.Image = Functions.drawbmp();
            label9.Text = Functions.updatePrice().ToString();

        }

        private void Form1_Load(object sender, EventArgs e)
        {

            comboColor1.Items.Clear();
            comboColor2.Items.Clear();
            comboColorTriple.Items.Clear();
            comboColorPinstripe.Items.Clear();

            comboColor1.Items.AddRange(Globals.colorNames);
            comboColor2.Items.AddRange(Globals.colorNames);
            comboColorTriple.Items.AddRange(Globals.colorNames);
            comboColorPinstripe.Items.AddRange(Globals.colorNames);

            comboColor1.SelectedIndex = 0;
            comboColor2.SelectedIndex = 0;
            comboColorTriple.SelectedIndex = 0;
            comboColorPinstripe.SelectedIndex = 0;

            radio70.Select();
            Globals.lenght = 70.0;

            radio16.Select();
            Globals.strands = 16;
            
            radioNone.Select();
            Globals.discount = 0;

        }

        private void label9_Click(object sender, EventArgs e)
        {
            // Assuming colorNames array is defined in the Globals class
            int indexFluorescentGreen = Array.IndexOf(Globals.colorNames, "Fluorescent Green");
            int indexBlack = Array.IndexOf(Globals.colorNames, "Black");
            int indexWhite = Array.IndexOf(Globals.colorNames, "White");

            // Declare the int array with specified indices
            int[] colorIndices = new int[16]
            {
                indexFluorescentGreen, indexFluorescentGreen, indexFluorescentGreen,
                indexFluorescentGreen, indexFluorescentGreen, indexFluorescentGreen,
                indexFluorescentGreen, indexBlack, indexWhite, indexWhite, indexWhite,
                indexWhite, indexWhite, indexWhite, indexWhite, indexBlack
            };

            previewBox.Image = Functions.drawbmp();
            label9.Text = Functions.updatePrice().ToString();

        }

        private void radioSociety_CheckedChanged(object sender, EventArgs e)
        {
            Globals.discount = -1;
            previewBox.Image = Functions.drawbmp(); 
            label9.Text = Functions.updatePrice().ToString();
        }

        private void radioNone_CheckedChanged(object sender, EventArgs e)
        {
            Globals.discount = 0;
            previewBox.Image = Functions.drawbmp();
            label9.Text = Functions.updatePrice().ToString();
        }

        private void comboBox1_SelectedIndexChanged(object sender, EventArgs e)
        {
            Globals.discount = int.Parse(comboBox1.Text);
            previewBox.Image = Functions.drawbmp();
            label9.Text = Functions.updatePrice().ToString();
        }

        private void radio66_CheckedChanged(object sender, EventArgs e)
        {
            Globals.lenght = 66.00;
            previewBox.Image = previewBox.Image = Functions.drawbmp();
            label9.Text = Functions.updatePrice().ToString();
        }

        private void radio68_CheckedChanged(object sender, EventArgs e)
        {
            Globals.lenght = 68.00;
            previewBox.Image = previewBox.Image = Functions.drawbmp();
            label9.Text = Functions.updatePrice().ToString();
        }

        private void radio70_CheckedChanged(object sender, EventArgs e)
        {
            Globals.lenght = 70.00;
            previewBox.Image = Functions.drawbmp();
            label9.Text = Functions.updatePrice().ToString();
        }

        private void radio72_CheckedChanged(object sender, EventArgs e)
        {
            Globals.lenght = 72.00;
            previewBox.Image = Functions.drawbmp();
            label9.Text = Functions.updatePrice().ToString();
        }

        private void lenghtBox_TextChanged(object sender, EventArgs e)
        {
            if (lenghtBox.Text != "") Globals.lenght = float.Parse(lenghtBox.Text);
            else radio70.Checked = true;

            previewBox.Image = Functions.drawbmp();
            label9.Text = Functions.updatePrice().ToString();
        }

        private void radio14_CheckedChanged(object sender, EventArgs e)
        {
            Globals.strands = 14;
            previewBox.Image = Functions.drawbmp();
            label9.Text = Functions.updatePrice().ToString();
        }

        private void radio16_CheckedChanged(object sender, EventArgs e)
        {
            Globals.strands = 16;
            previewBox.Image = Functions.drawbmp();
            label9.Text = Functions.updatePrice().ToString();
        }

        private void radio18_CheckedChanged(object sender, EventArgs e)
        {
            Globals.strands = 18;
            previewBox.Image = Functions.drawbmp();
            label9.Text = Functions.updatePrice().ToString();
        }

        private void threadBox_TextChanged(object sender, EventArgs e)
        {
            if (threadBox.Text != "") Globals.strands = int.Parse(threadBox.Text);
            else radio16.Checked = true;

            previewBox.Image = Functions.drawbmp(); 
            label9.Text = Functions.updatePrice().ToString();
        }

        private void comboColor1_SelectedIndexChanged(object sender, EventArgs e)
        {
            if(comboColor1.SelectedIndex != -1)
            {
                Globals.selCol1 = comboColor1.SelectedIndex;
                previewBox.Image = Functions.drawbmp(); 
                label9.Text = Functions.updatePrice().ToString();
            }
        }

        private void comboColor2_SelectedIndexChanged(object sender, EventArgs e)
        {
            if (comboColor2.SelectedIndex != -1)
            {
                Globals.selCol2 = comboColor2.SelectedIndex;
                previewBox.Image = Functions.drawbmp(); 
                label9.Text = Functions.updatePrice().ToString();
            }
        }

        private void comboColor3_SelectedIndexChanged(object sender, EventArgs e)
        {
           
        }

        private void comboColor3_SelectedIndexChanged_1(object sender, EventArgs e)
        {
        }

        private void comboColor3_SelectedIndexChanged_2(object sender, EventArgs e)
        {
            
        }

        private void comboColorTriple_SelectedIndexChanged(object sender, EventArgs e)
        {
            if (comboColorTriple.SelectedIndex != -1)
            {
                Globals.selCol3 = comboColorTriple.SelectedIndex;
                previewBox.Image = Functions.drawbmp(); 
                label9.Text = Functions.updatePrice().ToString();
            }
        }

        private void comboColorPinstripe_SelectedIndexChanged(object sender, EventArgs e)
        {
            if (comboColorPinstripe.SelectedIndex != -1)
            {
                Globals.selCol4 = comboColorPinstripe.SelectedIndex;
                previewBox.Image = Functions.drawbmp(); 
                label9.Text = Functions.updatePrice().ToString();
            }
        }

        private void radioFriend_CheckedChanged(object sender, EventArgs e)
        {
            Globals.discount = -2;
            previewBox.Image = Functions.drawbmp();
            label9.Text = Functions.updatePrice().ToString();
        }

        private void previewBox_Click(object sender, EventArgs e)
        {

        }
    }
}
