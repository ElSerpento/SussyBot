# SussyBot
SussyBot is a bot made with the discordpy module for the discord API. It can do image manipulation, and has commands to help coordinate events between server members. Every image made through the bot is uploaded to Imgur through its JSON API. It's also slightly dubious.

# Commands
Below is a list of available commands for sussy, by category:

### Alert Commands
.sendalert – Sends an alert message  
.setchannel – Sets a channel for alerts to be sent to  
.timezone – Shows working timezone (kind of)  

### Image Commands
.contentaware – Contentawares an image  
.deepfry – Deepfries an image  
.hueshift – Hue shifts an image  
.mirror - Mirrors images, on either side.  
.random - Pulls a random image out of various sites  

### Roles
.roleopt - Hand out roles via reaction

# Database
It uses an SQLite3 database to keep data between instances of the bot, like the alerts set on each server the bot is in. The schema for this database is as follows:
### shout_channel:
| channel_id  | guild_id |
| ------------- |:-------------:|
 INTEGER | INTEGER
### notif_user:
| alert_id  | user_id |
| ------------- |:-------------:|
 INTEGER | INTEGER
### alert:
| channel_id | message_id | alert_time | label |
| -------------|-------------|-------------|:-------------:|
 INTEGER | INTEGER | TIMESTAMP | TEXT
### rolepost:
| msg_id | role_id |
|--------|---------|
 INTEGER |  INTEGER
