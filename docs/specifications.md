**WEBSITE SPECIFICATIONS**

*Main Goal: Creating a "personal page" website that can be used to see my work and provide access to some services. Some open, some requiring an account. The language must be selectable between EN and IT with preference on IT. Texts, descriptions and other written elements must come from a table or similar to allow easy translation and maintenance. The UI should always be responsive and able to be used both on web and mobile.*

*Limitations: The system needs to be able to run on an ARM based SBC like an OrangePi, with limited CPU and RAM usage. Concurrent user count is expected to be very low. Python or nginx based website frameworks can be usable, it is crucial to make it easily serviceable. Now there is Grav installed, so if doable use that, otherwise provide alternatives that are docker friendly.*

*UI specs: use a darker purple and dark grey color scheme. Use orange instead of purple if it could fit better. Use shades of grey for most of the UI when in dark theme. In dark mode all UI should be consistent, including headers etc.*

---

*1. Common UI (desktop/web version):*
- **Top header**, with logo in the left side, navbar with sections and on the right the shop icon and a user area with login button. Also add a light/dark theme selector.
- When logged in, the user area has the user image, username and a dropdown menu to logout or change settings.
- When logged out, only a "login" option must be available.
- When logged in, the settings menu should contain basic settings like user image, name, password change and (if it is) a badge indicating it belongs to the Arcieri Carraresi club.
- **Bottom header** must be divided in three columns, each with centered text: the first containing links to the website sections, the second has a "newsletter" form available, the third has "useful links" each with their respective logos (found on /media) such as:
  - My own printables page [https://www.printables.com/@TheIgorMC]
  - My github page [https://github.com/TheIgorMC]
  - The FITARCO page of my results [https://www.fitarco-italia.org/arcieri/situazione.php?Codice=93229]
  - A Ko-Fi link for donations [https://ko-fi.com/theigormc]

Underneath this there is the privacy statements, copyright etc for "Orion Project" from 2024 to the current year.

---

*2. Home page (desktop/web versions):*
Needs to provide a 3-column welcome screen area that allows to select one of the three macro areas of interest:
- Archery: where a brief header is used to point at the fact that you can use the analysis tool to analyze your stats, while the competition subscription is limited to authorized accounts (used to register my club, the ASD Compagnia Arcieri Carraresi, members to competitions.) There also is a shop for custom grips, strings and so on.
- 3D printing: This section will have a gallery of my work, a quote tool (registered users only) and a shop.
- Electronics: Where i will have a show of my projects and a shop for some of those.

Graphically, the UI should be with a background section and the three images for the three areas of interest in "rectangular bubbles" that animate to zoom in, turn from B&W to color and pop up the descriptive section when hovered. 
Then a "About me" section underneath this selector with some spacing, with a short description of who i am and why i do what i do.

---

*2A. Admin page (desktop/web versions):*
An admin page/panel will be used to see all usernames and edit the club status, then also allow for gallery entries to be inserted  with name, description and images. Both for 3d prints and electronics.
Here the shop entries will also reside when the shop will be online.

*3. Section pages (desktop/web versions):*
The sections should be as follows:
- Archery section: similar to the homepage with navigation to the different services listed above. Same UI styling with B&W images zooming in etc.
- 3D printing and electronic sections: Unlike the archery section and main page, it should be a gallery of my works with underneath the option to go to the relative subsections (with a short description of what each one covers). 

---

*4. Archery analysis section (All UI variants):*
In this section there should be an intuitive and simple way to analyze one's results in competitions and view relevant statistics.
The page will be deeply linked with a database via an API. The API needs to be reached via Cloudflare access tokens on the address api.orion-project.it and allows several commands, found on the file "APIspec.json". Modifications where needed can be applied.
The data can be used to populate fields (for example competition types) and to search and interrogate the database (like searching an athlete).
Data like the results for a specific competition type need to then be plotted, with an appropriate graphical element that allows easy navigation and understanding of the data. It needs to update if the filter changes either for dates or competition types.
A "evaluate average" flag must be provided to gather the average per competition. To do so, a table or csv with the association competition -> arrow count needs to be created.
The section must allow to compare up to 5 athletes on the same graph, select a period of interest and filter either by macro categories (indoor, outdoor...) Or by specific competition type. Associations between categories and competition types will be done via a csv file or table to be created.
Statistics section must be showing several informations, like the number of competitions an athlete has participated in, distribution of medals and percentage of the scorers (like 5th out of 50 would be a top 10%, this stat needs to be present too, like "average finish in the last 10 competitions: 24% of shooters"). Medals, best score by competition type etc all need to be provided. If a specific kind of competition or timeframe is selected, then another statistics section will be used, to show the data for that timeframe.

---

*4. Archery competition manager (All UI variants):*
In this section users logged in that belong to the ASD Compagnia Arcieri Carraresi (They need to be authorized by me beforehand in an admin console) can select which competitions to take part in. There should be a list gathered from the API of the competitions with active subscriptions, the ones with invites published and subscriptions not yet open and the ones with no invite yet published. Subscriptions are not automatic "you are in" mechanisms, they just allow the ones handling subscriptions to have a list to work from.
The system should:
- For competitions with subscriptions already open and active, allow the user to select a turn and  subscribe to be booked for that turn.
- For competitions with only invite published but no active booking, allow to select a turn and subscribe to be booked.
- For competitions without invite, they will only be able to register "interest" and will NEED to provide further informations when the invite is published. A mail and/or telegram message can be sent automatically when the scanner sees the invite published (managed in a different script).