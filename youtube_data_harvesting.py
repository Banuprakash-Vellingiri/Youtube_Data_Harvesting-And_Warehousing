#------------------------------------- Youtube Data Harvesting And Warehousing ------------------------------------------------------------
#Importing neccessary packages
import mysql.connector
import pymongo
import googleapiclient.discovery
import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
from sqlalchemy import create_engine
from PIL import Image
from datetime import datetime
import re
import plotly_express as px
#------------------------------------------------------------------------------------------------------------------------------------
#Connecting with Youtube using API
api_key="AIzaSyDsWfd2BRAygrfLEQRbCXF4h6_CGhsduZE"
youtube = googleapiclient.discovery.build("youtube","v3",developerKey=api_key)
#------------------------------------------------------------------------------------------------------------------------------------
# Connecting to MongoDB

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["mongodb_youtube_database"]
#Creating the collectoions
col1 = db["channel_data"]
col2 = db["video_data"]
col3 = db["comment_data"]
#------------------------------------------------------------------------------------------------------------------------------------
#Function to get the channel_details:  
@st.cache_data
def get_channel_statistics(_youtube,channel_ids):
    all_data = []
    request = youtube.channels().list(
    part="snippet,contentDetails,statistics",
    id=channel_ids)
    response = request.execute()

    for i in range(len(response["items"])):
        data = dict(channel_id = response["items"][i]["id"],
                    channel_name = response["items"][i]["snippet"]["title"],
                    channel_views = response["items"][i]["statistics"]["viewCount"],
                    subscriber_count = response["items"][i]["statistics"]["subscriberCount"],
                    total_videos = response["items"][i]["statistics"]["videoCount"],
                    playlist_id = response["items"][i]["contentDetails"]["relatedPlaylists"]["uploads"])
        all_data.append(data)
    return all_data

#Creating a function to get playlist data
@st.cache_data
def get_playlist_data(df):
    playlist_ids = []
     
    for i in df["playlist_id"]:
        playlist_ids.append(i)

    return playlist_ids

#Creating a function to get video ids
@st.cache_data
def get_video_ids(_youtube,playlist_id_data):
    video_id = []

    for i in playlist_id_data:
        next_page_token = None
        more_pages = True

        while more_pages:
            request = youtube.playlistItems().list(
                        part = 'contentDetails',
                        playlistId = i,
                        maxResults = 50,
                        pageToken = next_page_token)
            response = request.execute()
            
            for j in response["items"]:
                video_id.append(j["contentDetails"]["videoId"])
        
            next_page_token = response.get("nextPageToken")
            if next_page_token is None:
                more_pages = False
    return video_id
        

#Creating a function to get Video details
@st.cache_data
def get_video_details(_youtube,video_id):

    all_video_stats = []

    for i in range(0,len(video_id),50):
        
        request = youtube.videos().list(
                  part="snippet,contentDetails,statistics",
                  id = ",".join(video_id[i:i+50]))
        response = request.execute()
        
        for video in response["items"]:
            #Formatting date
            published_dates = video["snippet"]["publishedAt"]
            parsed_dates = datetime.strptime(published_dates, "%Y-%m-%dT%H:%M:%SZ")
            format_date = parsed_dates.strftime('%Y-%m-%d')
            # Function to convert duration int0 HH:MM:SS
            def convert_duration(durat):
                    regex = r'PT(\d+H)?(\d+M)?(\d+S)?'
                    match = re.match(regex, durat)
                    if not match:
                        return '00:00:00'
                    hours, minutes, seconds = match.groups()
                    hours = int(hours[:-1]) if hours else 0
                    minutes = int(minutes[:-1]) if minutes else 0
                    seconds = int(seconds[:-1]) if seconds else 0
                    total_seconds = hours * 3600 + minutes * 60 + seconds
                    return '{:02d}:{:02d}:{:02d}'.format(int(total_seconds / 3600), int((total_seconds % 3600) / 60), int(total_seconds % 60))
            
            durat= video["contentDetails"]["duration"]
            # convert_duration(durat)
            videos = dict(video_id = video["id"],
                          channel_id = video["snippet"]["channelId"],
                         video_name = video["snippet"]["title"],
                         channel_title=video["snippet"]["channelTitle"],
                         published_date = format_date,
                         view_count = video["statistics"].get("viewCount",0),
                         like_count = video["statistics"].get("likeCount",0),
                         comment_count= video["statistics"].get("commentCount",0),
                         duration = convert_duration(durat))
                         # Define a function to convert duration
            
            all_video_stats.append(videos)

    return (all_video_stats)

#Creating a function to get comment details
@st.cache_data
def get_comments(_youtube,video_ids):
    comments_data= []
    try:
        next_page_token = None
        for i in video_ids:
            while True:
                request = youtube.commentThreads().list(
                    part = "snippet,replies",
                    videoId = i,
                    textFormat="plainText",
                    maxResults = 100,
                    pageToken=next_page_token)
                response = request.execute()

                for item in response["items"]:
                    published_date= item["snippet"]["topLevelComment"]["snippet"]["publishedAt"]
                    parsed_dates = datetime.strptime(published_date,'%Y-%m-%dT%H:%M:%SZ')
                    format_date = parsed_dates.strftime('%Y-%m-%d')
                    

                    comments = dict(comment_id = item["id"],
                                    video_id = item["snippet"]["videoId"],
                                    comment_text = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"],
                                    comment_author = item["snippet"]["topLevelComment"]["snippet"]["authorDisplayName"],
                                    comment_published_date = format_date)
                    comments_data.append(comments) 
                
                next_page_token = response.get('nextPageToken')
                if next_page_token is None:
                    break       
    except Exception as e:
        print("An error occured",str(e))          
            
    return comments_data
#------------------------------------------------------------------------------------------------------------------------------------
 #Creating a function to get Channel name list

def channel_names():   
    all_channel_names = []
    for i in db.channel_data.find():
        all_channel_names.append(i['channel_name'])
    return all_channel_names 
#------------------------------------------------------------------------------------------------------------------------------------
#Setting  streamlit environment

#Page congiguration
page_logo = Image.open("youtube_chart.png")
st.set_page_config(page_title= "Youtube Data Harvesting and Warehousing by Banuprakash V",
                 
                   page_icon= page_logo,
                   layout= "wide",
                   initial_sidebar_state= "expanded")
#Side bar configuration
channel_list=[]
with st.sidebar:
    selected = option_menu("Menu", ["Home","Extract and Transform","Queries"], 
                           icons=["house","arrow-left-right","card-list"],
                           default_index=0,
                           orientation="vertical",
                           styles={"nav-link": {"font-size": "20px", "text-align": "centre", "margin": "5px", 
                                                "--hover-color": "grey"},
                                   "icon": {"font-size": "20px"},
                                   "container" : {"max-width": "600px"},
                                   "nav-link-selected": {"background-color": "orange"}})
#------------------------------------------------------------------------------------------------------------------------------------
#Home page

if selected == "Home":

        st.info("## :white[Youtube Data Harvesting And Warehousing]")
        col1,col2 = st.columns(2,gap="medium")
        col1.markdown("### :orange[Technologies Used :]")
        col1.markdown("### :white[ &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;1.&nbsp;Python]")
        col1.markdown("### :white[ &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;2.&nbsp;Youtube Data API]")
        col1.markdown("### :white[ &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;3.&nbsp;MongoDB]")
        col1.markdown("### :white[ &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;4.&nbsp;MYSQL]")
        col1.markdown("### :white[ &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;4.&nbsp;Streamlit]")
        col1.markdown("### :orange[Synopsis:]")
        col1.markdown("### :white[:blue[Step 1]: Retrieving the Youtube channels data from Youtube data API.]")
        col1.markdown("### :white[:blue[Step 2]: Storing the data into MongoDB.]")
        col1.markdown("### :white[:blue[Step 3]: Migrating and transforming the data from MongoDb to SQL database.]")
        col1.markdown("### :white[:blue[Step 4]: Querying the data and displaying it in Streamlit application.]")
        col2.write("#   ")
        col2.write("#   ")
        col2.write("#   ")
        col2.image("data_image.png")
    

#------------------------------------------------------------------------------------------------------------------------------------
#Extracting the data from Youtube

if selected == "Extract and Transform":
    st.info("## Extract and transform data")
    tab1,tab2= st.tabs(["# :orange[EXTRACT ] ",":orange[TRANSFORM]"])    
    
    #Extract tab
    with tab1:
        st.markdown("#    ")
        st.markdown("### :blue[ Enter Channel ID :]")
        channel_ids= st.text_input(" Kindly input valid ID")
        channel_lis = [channel_ids]
        for i in channel_lis:
             channel_list.append(i)

        #Creating the Extract Button
        extract_button_1=st.button("Extract data from Youtube")
        if channel_ids and extract_button_1:
            channel_details =get_channel_statistics(youtube,channel_ids)
            a=[]
            for i in range(len(channel_details)):
                a.append(channel_details[i]["channel_name"])
            st.write("### Details of the channel  &nbsp; :red[{}] &nbsp; :".format((', '.join(a))))
            st.table(channel_details)

        #Setting upload button for Mongodb   
        extract_button_2=st.button("Upload data to MongoDB")
        if extract_button_2:
          with st.spinner('On progress please wait....'):
            
            channel_details = get_channel_statistics(youtube,channel_ids)
            df = pd.DataFrame(channel_details) 
            playlist_id_data = get_playlist_data(df)
            video_id = get_video_ids(youtube,playlist_id_data)
            video_details = get_video_details(youtube,video_id)
            get_comment_data = get_comments(youtube,video_id) 
  
            #Inserting the data into MongoDB collections 
  
            col1.insert_many(channel_details) 
            col2.insert_many(video_details)
            col3.insert_many(get_comment_data)

            st.success("Data uploaded Successfully.....")
   #Transform tab
    with tab2: 
          def channel_names():   
                    ch_name = []
                    for i in db.channel_data.find():
                        ch_name.append(i['channel_name'])
                    return ch_name
          st.markdown("### Transform data to SQL")
          channel_name_list=channel_names()
          user_input =st.multiselect("Select the channel to be inserted into MySQL Tables",options = channel_name_list)

          #Creating a upload button for transferring the data into MYSQL
          upload_button=st.button("Upload data into MySQL")
          if upload_button:  
             with st.spinner('Please wait uploading... '):
                    
                    #Fetching Channel details:     
                    def get_channel_details(user_input,col1):
                                query = {"channel_name":{"$in":list(user_input)}}
                                projection = {"_id":0,"channel_id":1,"channel_name":1,"channel_views":1,"subscriber_count":1,"total_videos":1,"playlist_id":1}
                                x = col1.find(query,projection)
                                channel_table = pd.DataFrame(list(x))
                                return channel_table

                    channel_data = get_channel_details(user_input,col1)
                    # print(channel_data)
                    st.write(channel_data)
                            
                        
                    #Fetching Video details:
                    def get_video_details(channel_list,col2):
                                query = {"channel_id":{"$in":channel_list}}
                                projection = {"_id":0,"video_id":1,"channel_id":1,"video_name":1,"channel_title":1,"published_date":1,"view_count":1,"like_count":1,"comment_count":1,"duration":1}
                                x = col2.find(query,projection)
                                video_table = pd.DataFrame(list(x))
                                return video_table

                    video_data = get_video_details(channel_list,col2)
                    # print(video_data)
                
                    #Fetching Comment details:
                    def get_comment_details(video_ids,col3):
                                query = {"video_id":{"$in":video_ids}}
                                projection = {"_id":0,"comment_id":1,"video_id":1,"comment_text":1,"comment_author":1,"comment_published_date":1}
                                x = col3.find(query,projection)
                                comment_table = pd.DataFrame(list(x))
                                return comment_table

                    # Fetch video_ids from mongoDb
                    video_ids = video_data["video_id"].to_list() 
                    comment_data = get_comment_details(video_ids,col3)       
                    client.close()  
#------------------------------------------------------------------------------------------------------------------------------------
                    #Connecting to MySQL Database 
                    mysql_database = mysql.connector.connect(
                                host = "localhost",
                                port=3306,
                                user = "root",
                                password = "952427",
                                database = "sql_youtube_database")

                    cursor = mysql_database.cursor()

#------------------------------------------------------------------------------------------------------------------------------------
                    #Creating an SQLAlchemy engine to connect to the MYSQL database:
                    engine = create_engine('mysql+mysqlconnector://root:952427@localhost/sql_youtube_database')
#------------------------------------------------------------------------------------------------------------------------------------
                    # Inserting Channel data :
                    try:
                       
                        channel_data.to_sql('channel_data', con=engine, if_exists='append', index=False, method='multi')
                        print("Channel data uploaded successfully")
                    except Exception as e:
                        if 'Duplicate entry' in str(e):
                            print("Duplicate data found")
                        else:
                            print("Error occurred:", e)
                    st.success("Channel data uploaded successfully")
                    engine.dispose()

                # Inserting Video data :
                    try:
                        video_data.to_sql('video_data', con=engine, if_exists='append', index=False, method='multi')
                        print("Video data uploaded successfully")
                    except Exception as e: 
                        if 'Duplicate entry' in str(e):
                            print("Duplicate data found")
                        else:
                             print("Error occurred:", e)
                    st.success("Video data uploaded successfully")

                    engine.dispose()

                    # Inserting comment data :

                    try:
                        comment_data.to_sql('comment_data', con=engine, if_exists='append', index=False, method='multi')
                        print("Comment data uploaded successfully")
                    except Exception as e: 
                        if 'Duplicate entry' in str(e):
                            print("Duplicate data found.")
                        else:
                            print("Error occurred:", e)
                    st.success("Comment data uploaded successfully")

                    engine.dispose()
 #------------------------------------------------------------------------------------------------------------------------------------                   
#Queries 
if selected=="Queries": 
            #Connecting to MYSQL database                
            mysql_database= mysql.connector.connect(
                    host = "localhost",
                    port=3306,
                    user = "root",
                    password = "952427",
                    database = "sql_youtube_database")

            cursor =mysql_database.cursor()
  #------------------------------------------------------------------------------------------------------------------------------------          
            st.info("## Quries Section")
            questions = st.selectbox("Select the questions given below:",
                                    [' Click the question that you would like to query',
                                    '1. What are the names of all the videos and their corresponding channels?',
                                    '2. Which channels have the most number of videos, and how many videos do they have?',
                                    '3. What are the top 10 most viewed videos and their respective channels?',
                                    '4. How many comments were made on each video, and what are their corresponding video names?',
                                    '5. Which videos have the highest number of likes, and what are their corresponding channel names?',
                                    '6. What is the total number of likes for each video, and what are their corresponding video names?',
                                    '7. What is the total number of views for each channel, and what are their corresponding channel names?',
                                    '8. What are the names of all the channels that have published videos in the year 2022?',
                                    '9.What is the average duration of all videos in each channel, and what are their corresponding channel names?',
                                    '10. Which videos have the highest number of comments, and what are their corresponding channel names?'
                                    ])
                                    
            if questions == '1. What are the names of all the videos and their corresponding channels?':
                query1 = "select channel_name as Channel_names ,video_name as Video_names from channel_data c join video_data v on c.channel_id = v.channel_id;"
                cursor.execute(query1)

            #Storing the results in Pandas Dataframe:
                result1 = cursor.fetchall()
                table1 = pd.DataFrame(result1,columns = cursor.column_names)
                st.table(table1)

            elif questions == '2. Which channels have the most number of videos, and how many videos do they have?':
                query2 = "select channel_name as Channel_names,count(video_name) as Most_Number_of_Videos from video_data v join channel_data c on c.channel_id = v.channel_id group by channel_name order by count(video_name) desc;"
                cursor.execute(query2)
                result2 = cursor.fetchall()
                table2 = pd.DataFrame(result2,columns =cursor.column_names)           
                st.table(table2)
                fig = px.bar(table2,
                     x=cursor.column_names[0],
                     y=cursor.column_names[1],
                     orientation='v',
                    )
                st.plotly_chart(fig)
  

            elif questions == '3. What are the top 10 most viewed videos and their respective channels?':
                query3 = "select channel_name as Channel_names,video_name as Video_names,view_count as Top_10_Viewed_Videos from channel_data c join video_data v on c.channel_id = v.channel_id order by view_count desc limit 10;"
                cursor.execute(query3)
                result3 = cursor.fetchall()
                table3 = pd.DataFrame(result3,columns=cursor.column_names)
                st.table(table3)
                fig = px.bar(table3,
                     x=cursor.column_names[1],
                     y=cursor.column_names[2],
                     orientation='v',
                    )
                st.plotly_chart(fig)
                
            
            
            elif questions == '4. How many comments were made on each video, and what are their corresponding video names?':
                query4 = "select channel_name as Channel_names, video_name as Video_names,comment_count as Comments_Count from video_data v join channel_data c on c.channel_id = v.channel_id order by comment_count desc;"
                cursor.execute(query4)
                result4 = cursor.fetchall()
                table4 = pd.DataFrame(result4,columns=cursor.column_names)
                st.table(table4)
                fig = px.bar(table4,
                     x=cursor.column_names[1],
                     y=cursor.column_names[2],
                     orientation='v',
                    )
                st.plotly_chart(fig)
                
                

            elif questions == '5. Which videos have the highest number of likes, and what are their corresponding channel names?':
                query5 = "select channel_name as Channel_names,video_name as Video_names,like_count as Number_of_likes from video_data v join channel_data c on c.channel_id = v.channel_id order by like_count desc;"
                cursor.execute(query5)
                result5 = cursor.fetchall()
                table5 = pd.DataFrame(result5,columns=cursor.column_names)
                st.table(table5)
                fig = px.bar(table5,
                     x=cursor.column_names[0],
                     y=cursor.column_names[2],
                     orientation='v',
                    )
                st.plotly_chart(fig)
                

            elif questions == '6. What is the total number of likes for each video, and what are their corresponding video names?':
                query6 = "select channel_name as Channel_names,video_name as Video_names,like_count as Like_count from video_data v join channel_data c on c.channel_id = v.channel_id order by like_count desc;"
                cursor.execute(query6)
                result6 = cursor.fetchall()
                table6 = pd.DataFrame(result6,columns=cursor.column_names)
                st.table(table6)
                fig = px.bar(table6,
                     x=cursor.column_names[0],
                     y=cursor.column_names[2],
                     orientation='v',
                    )
                st.plotly_chart(fig)

            elif questions == '7. What is the total number of views for each channel, and what are their corresponding channel names?':
                query7 = "select channel_name as Channel_names,channel_views as Total_No_of_views from channel_data"
                cursor.execute(query7)
                result7= cursor.fetchall()
                table7 = pd.DataFrame(result7,columns=cursor.column_names)
                st.table(table7)
                fig = px.bar(table7,
                     x=cursor.column_names[1],
                     y=cursor.column_names[0],
                     orientation='v',
                    )
                st.plotly_chart(fig)
    

            elif questions == '8. What are the names of all the channels that have published videos in the year 2022?':

                query8 = "select distinct c.channel_name as Channel_names,year(published_date) as Published_year from channel_data c join video_data v on c.channel_id = v.channel_id where year(published_date) = 2022;"
                cursor.execute(query8)
                result8 = cursor.fetchall()
                table8 = pd.DataFrame(result8,columns=cursor.column_names)
                st.table(table8)
                fig = px.bar(table8,
                     x=cursor.column_names[0],
                     y=cursor.column_names[1],
                     orientation='v',
                    )
                st.plotly_chart(fig)

            elif questions=='9.What is the average duration of all videos in each channel, and what are their corresponding channel names?':
                 query9="""SELECT channel_title AS Channel_names,
                        AVG( TIME_TO_SEC(SUBTIME(duration, '00:00:00')) / 60) AS "Average_video_duration (mins)"
                            FROM video_data
                            GROUP BY channel_title
                            ORDER BY  AVG( TIME_TO_SEC(SUBTIME(duration, '00:00:00')) / 60) DESC"""
                 cursor.execute(query9)
                 result9=cursor.fetchall()
                 table9 = pd.DataFrame(result9, columns=cursor.column_names)
                 st.table(table9)
                 fig = px.bar(table9,
                     x=cursor.column_names[0],
                     y=cursor.column_names[1],
                     orientation='v',
                    )
                 st.plotly_chart(fig)
            elif questions =='10. Which videos have the highest number of comments, and what are their corresponding channel names?':
                query10 = "select channel_name as Channel_names,video_name as Video_names,comment_count as Highest_No_of_comments from channel_data c join video_data v on c.channel_id = v.channel_id order by comment_count desc limit 10;"
                cursor.execute(query10)
                result10 = cursor.fetchall()
                table10 = pd.DataFrame(result10,columns=cursor.column_names)
                st.table(table10)
                fig = px.bar(table10,
                     x=cursor.column_names[0],
                     y=cursor.column_names[2],
                     orientation='v',
                    )
                st.plotly_chart(fig)
                

#Finally closing the connection of SQL database:
#------------------------------------------------------------------------------------------------------------------------------------
                cursor.close()
