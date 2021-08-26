# SussyBot
SussyBot is a bot made with the discordpy module for the discord API. It can do image manipulation, and has alert commands to help coordinate events between server members. It's also slightly dubious.

It uses an SQLite3 database to keep data between instances of the bot, like the alerts set on each server the bot is in. The schema for this database is as follows:

#### shout_channel
| channel_id  | guild_id |
| ------------- |:-------------:|
 INTEGER | INTEGER
#### notif_user
| alert_id  | user_id |
| ------------- |:-------------:|
 INTEGER | INTEGER
#### alert
| channel_id | message_id | alert_time | label |
| -------------|-------------|-------------|:-------------:|
 INTEGER | INTEGER | TIMESTAMP | TEXT
#### rolepost
| msg_id | role_id |
|--------|---------|
 INTEGER |  INTEGER