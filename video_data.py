from googleapiclient.discovery import build
import re
from datetime import timedelta,date


# Service is Youtube API 
api_key = 'AIzaSyDbBHaLv3JAFa5d4zVQFz_uzqKszztI8kw'
youtube = build('youtube', 'v3', developerKey=api_key)


hours_pattern = re.compile(r'(\d+)H')
minutes_pattern = re.compile(r'(\d+)M')
seconds_pattern = re.compile(r'(\d+)S')
datePosted_pattern = re.compile(r'([\d]+)\-([\d]+)\-([\d]+)T')

# showTitle_pattern = re.compile('Joe Rogan Experience ([\#]?[\d]+) - (\w+\s\w+)\s?\&?\&?\s?(\w+\s\w+)?') 
showTitle_pattern = re.compile('Joe Rogan Experience [\#]?([\d]+) - (\w+\s\w+)\s?\&?\&?\s?(\w+\s\w+)?') 

showNums, guestNames = [], []
videos_views = []
engagementFactors = []
contraversyFactors = []

uploadDates = []


# playlist = 'PL-osiE80TeTsWmV9i9c58mdDCSskIFdDS' # Pandas playlist Corey Schafer  


def channelPlaylist(channelID):

    ###################################################
    # Request to API (Channels and playlistItems) - fetch uploads playlist ID and video title
    ###################################################
    
    ch_response = youtube.channels().list(
        part="contentDetails",
        id=channelID,
    ).execute()
    
    # Extract ID of "Upload" playlist
    pl_ID_upload = ch_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    
    # infinite loop to get all videos in playlist
    videos,nextPageToken =  [], None

    while True: 
        pl_request = youtube.playlistItems().list(
            part = "snippet",
            playlistId = pl_ID_upload, 
            maxResults = 50, 
            pageToken = nextPageToken
        )
        pl_response = pl_request.execute()
        videos += pl_response['items']
                
        nextPageToken = pl_response.get('nextPageToken')
        if not nextPageToken: 
            break 

    for video in videos:
        title =  video['snippet']['title']
        showName = showTitle_pattern.search(title) 

        showNum = showName.group(1) if showName else -1
        showGuest = showName.group(2) if showName else "No guest found"
        showNums.append(int(showNum))
        guestNames.append(showGuest)

    

    ###################################################
    # Request to API (PlaylistItems) - fetch all videos in "upload" playlist  
    ###################################################
    
    nextPageToken = None
    while True: 
        pl_request = youtube.playlistItems().list(
            part = 'contentDetails',
            playlistId = pl_ID_upload, 
            maxResults = 50, 
            pageToken = nextPageToken
        )
        pl_response = pl_request.execute()

        videos_ID = [] # videos on current page 
        for item in pl_response['items']:
            vidID = item['contentDetails']['videoId']
            videos_ID.append(vidID)
        

        ###################################################
        # Request to API (Video) - fetch all Views and Enagagment metrics  
        ###################################################
        video_request = youtube.videos().list(
            part = 'statistics',
            id =','.join(videos_ID)  # Filter by pl vids, string-ified
        )
        vid_response = video_request.execute()

        for item in vid_response['items']:
            ### Views
            vidViews = int(item['statistics']['viewCount'])
            videos_views.append(vidViews) 

            ### engagementFactor = [(factor, likeCount, disklikeCount, commentCount)...]
            likeCount = int(item['statistics']['likeCount'])
            dislikeCount = int(item['statistics']['dislikeCount'])
            commentCount = int(item['statistics']['commentCount'])


            contraversyFactor = round(float(likeCount/(likeCount+dislikeCount)),2) # bubble color
            engagementFactor = round(float((likeCount+dislikeCount+commentCount)/vidViews),2) # bubble size
            
            
            # engagementFactor = round(float(likeCount/dislikeCount*commentCount),2)
            engagementFactors.append(engagementFactor)
            contraversyFactors.append(contraversyFactor)
            
            # engagementFactors.append(
            #     (engagementFactor,likeCount,dislikeCount,commentCount)
            # )


        ###################################################
        # Date Uploaded and Guest Name 
        ###################################################

        vid_response = youtube.videos().list(
            part = 'snippet',
            id =','.join(videos_ID), # Filter by pl vids, string-ified
        ).execute()

        for item in vid_response['items']:

            ### Date uploaded
            postedate = item['snippet']['publishedAt']
            postedate = datePosted_pattern.search(postedate) 

            year = int(postedate.group(1)) if postedate else 0
            month = int(postedate.group(2)) if postedate else 0
            day = int(postedate.group(3)) if postedate else 0
            uploadDate = date(year, month, day)
            uploadDates.append(uploadDate)

        
        nextPageToken = pl_response.get('nextPageToken')
        if not nextPageToken: 
            break 
    

    return showNums,guestNames,videos_ID,videos_views,engagementFactors,contraversyFactors,uploadDates

