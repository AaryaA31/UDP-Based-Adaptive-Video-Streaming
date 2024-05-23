[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-24ddc0f5d75046c5622901739e7c5dd533143b0c8e959d652212380cedb1ea36.svg)](https://classroom.github.com/a/7VnFugBz)
# CSEE 4119 Spring 2024, Assignment 1
## Aarya Agarwal
## GitHub username: AaryaA31

In the successful testing of my code: I executed it as follows:

python3 network.py 50000 127.0.0.1 60000 lab1-bw.txt .001
python3 server.py 60000
python3 client.py 127.0.0.1 60000 bunny 0.5

with the 3 commands run in seperate terminal tabs.

As the client runs, the log file is populated in the following format:
    log_entry = {start_time} {duration} {measured_bandwidth} {bandwidth} {bitrate} {filename}

In addition, the file structure used at the time of testing is as follows

-root
   - network.py
   - server.py
   - client.py
   - data
     - bunny

such that the video file is inside a data folder within the root file(relative to client and network)



I had some toruble making sure the entire chunk was received and used the size parameter described here to make sure data wasn't lost:
https://stackoverflow.com/questions/56813704/socket-programming-python-how-to-make-sure-entire-message-is-received

