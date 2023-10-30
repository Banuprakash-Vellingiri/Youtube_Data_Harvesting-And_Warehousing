#  Youtube_Data_Harvesting-And_Warehousing

**Aim:**

 The aim of this project is to allow users to access and analyze data from multiple YouTube channels for  useful insights. 

**Technologies Used:**

The following technologies are used in this project are used to create an application that allows users to retrieve, store, and query various YouTube channel information.
- Python
- YouTube Data API
- Streamlit
- MongoDB 
- MySQL

**Approach:**
1. Streamlit app: Streamlit is good for quickly building data visualization and analysis tools.We can set up a streamlit environment  to create a simple UI where users can enter a YouTube channel ID, view channel details, and select channels to migrate to the data warehouse.

2. YouTube data API: We will utilize the YouTube data API to retrieve channel and video data. The Google API client library for Python will be used to make requests to the API, allowing us to gather the required data quickly and efficiently.

3. Data storage in  MongoDB : Once the data is retrieved from the YouTube API, we will store it in a MongoDB reservoir.Since it is suitable  for storing and handling unstructured data.

4. Migrate data to  MYSQL : we will migrate the stored unstructured data in MongoDB to a SQL data warehouse.Comparing with others SQL databases MySQL database, can be used for this purpose, creating a structured data and its query is very simple to use.

5. Query the SQL data warehouse: SQL queries are executed to join the tables in the SQL data warehouse and retrieve data for specific channels based on user input.SQLAlchemy in Python can be utilized to interact with the SQL database.

6. Display data in the Streamlit app: The final step involves displaying the retrieved data in the Streamlit app. Streamlit's built-in data visualization features will enable us to create charts and graphs, aiding users in analyzing the data effectively.


**References :**

- Streamlit Documentation: [https://docs.streamlit.io/](https://docs.streamlit.io/)
- YouTube API Documentation: [https://developers.google.com/youtube](https://developers.google.com/youtube)
- MongoDB Documentation: [https://docs.mongodb.com/](https://docs.mongodb.com/)
- SQLAlchemy Documentation: [https://docs.sqlalchemy.org/](https://docs.sqlalchemy.org/)
- Python Documentation: [https://docs.python.org/](https://docs.python.org/)

## Check out the video #linkedin:[https://www.linkedin.com/posts/banuprakash-v-a088a3191_youtubeabrdataabrharvestingabrandabrwarehousing-activity-7124802076911575040-nExR/?utm_source=share&utm_medium=member_desktop](https://www.linkedin.com/posts/banuprakash-v-a088a3191_youtubeabrdataabrharvestingabrandabrwarehousing-activity-7124802076911575040-nExR/?utm_source=share&utm_medium=member_desktop)
