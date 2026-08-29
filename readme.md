# very very simple project please do not judge me or roast me



store is a plain Python dictionary that holds all key-value data in memory. When the container restarts, the data disappears. fine for learning purposes.

NODE_NAME, PEERS, and MODE are pulled from environment variables so each container can have its own identity and know where its peers live. Docker Compose will inject these values later.