import threading
import socket
import re
import os 

MAILDIR = "~/Maildir"
DOMAIN = "lbp.com"
SERVER_IP = "10.81.4.216"
PORT = 2525

def smtp_client_server(client_socket, client_address):
    print("test") ###

    state = {
        "HELO": False,
        "MAIL": False,
        "RCPT": False,
        "DATA": False,
        "client_hostname": "",
        "client_domain": ""
    }

    def reset(state):
        state = {
            "HELO": False,
            "MAIL": False,
            "RCPT": False,
            "DATA": False,
            "client_hostname": "",
            "client_domain": ""
        }

    smtp_initiation = b"220 SMTP kh4rg0sh 1.0\n"
    client_socket.send(smtp_initiation)

    try: 
        while True:
            message = client_socket.recv(1024).strip().decode().split()
            
            if message[0] == "HELO":
                print("test HELO") ###

                if len(message) != 2:
                    error_message = b"501 Syntax: HELO hostname \n"
                    client_socket.send(error_message)

                else:
                    if state["HELO"]:
                        reset(state)

                    state["HELO"] = True
                    state["client_domain"] = message[1]
                        
                    accept_message = f"250 {DOMAIN} OK \n".encode()
                    client_socket.send(accept_message)

            elif message[0] == "MAIL" and message[1].startswith("FROM:<"):
                print("test MAIL FROM") ###

                if not state["HELO"]:
                    error_message = b"503 5.5.1 Error: send HELO first \n"
                    client_socket.send(error_message) 

                else:
                    if not state["MAIL"]:
                        if len(message) != 2:
                            error_message = b"501 5.5.4 Syntax: MAIL FROM:<address> \n"
                            client_socket.send(error_message)
                        
                        else:
                            syntaxcheck = re.match(r"FROM:<[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+.[a-zA-Z0-9-.]+>$", message[1], re.IGNORECASE)

                            if not syntaxcheck:
                                error_message = b"501 5.1.7 Bad sender address syntax \n"
                                client_socket.send(error_message)

                            else:
                                state["MAIL"] = True

                                client_hostname, client_domain = message[1][len("FROM:<"):-len(">")].split("@")
                                state["client_hostname"] = client_hostname
                                state["client_domain"] = client_domain

                                mail_transaction = b"250 2.1.0 OK \n"
                                client_socket.send(mail_transaction)

                    else: 
                        error_message = b"503 5.5.1 Error: nested MAIL command\n"
                        client_socket.send(error_message)
            
            elif message[0] == "RCPT" and message[1].startswith("TO:<"):
                print("test RCPT TO") ###

                if not state["MAIL"]:
                    error_message = b"503 5.1.1 Bad sequence of commands\n"
                    client_socket.send(error_message) 

                elif state["MAIL"] and state["HELO"]: 
                    if len(message) != 2:
                        error_message = b"501 5.5.4 Syntax: RCPT TO:<address> \n"
                        client_socket.send(error_message) 
                    
                    else:
                        syntaxcheck = re.match(r"TO:<[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+.[a-zA-Z0-9-.]+>$", message[1], re.IGNORECASE)

                        if not syntaxcheck:
                            error_message = b"501 5.1.7 Bad recipient address syntax \n"
                            client_socket.send(error_message)

                        else:

                            recipient_hostname, recipient_domain = message[1][len("TO:<"):-len(">")].split("@")
                            if recipient_hostname != "kh4rg0sh":
                                error_message = b"550 5.5.7 Error: no such user \n"
                                client_socket.send(error_message)

                            elif recipient_hostname == "kh4rg0sh" and recipient_domain != DOMAIN:
                                print("handle what if wrong recipient domain") ###

                            else:
                                state["RCPT"] = True

                                mail_transaction = b"250 2.1.0 OK \n"
                                client_socket.send(mail_transaction)

            elif message[0] == "DATA":
                print("test DATA") ###

                if state["HELO"] and state["MAIL"] and state["RCPT"]:
                    accept_message = b"354 End data with <CR><LF>.<CR><LF> \n"
                    client_socket.send(accept_message)

                    mail_dir = os.path.expanduser(MAILDIR + "/" + recipient_domain)
                    
                    if not os.path.isdir(mail_dir):
                        os.makedirs(mail_dir) 
                    
                    mail_sender = mail_dir + "/" + state["client_hostname"]
                    
                    if not os.path.isdir(mail_sender):
                        os.makedirs(mail_sender) 

                    counter = 1
                    while os.path.isfile(f"{mail_sender}/{counter}.txt"):
                        counter += 1
                    
                    open_file = open(f"{mail_sender}/{counter}.txt", "w")

                    while True:
                        data_message = client_socket.recv(1024).strip().decode()
                        
                        if data_message != ".":
                            open_file.write(data_message)
                            
                        else: 
                            open_file.close()
                            break 

                else: 

                    print("handle errors for data") 

            elif message[0] == "QUIT":
                quit_message = b"221 2.0.0 Bye \n"
                client_socket.send(quit_message)
                client_socket.close()

                return 

    except Exception as error:
        print(f"Error encountered: {error}")
    
    finally: 
        client_socket.close()

    return 


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (SERVER_IP, PORT)
    
    server.bind(server_address)
    server.listen()

    print(f"SMTP Server Running on port {PORT}")

    while True:
        client_socket, client_address = server.accept()
        print(f"Connection received from {client_address}")

        if client_socket:
            smtp_thread = threading.Thread(target=smtp_client_server, args=(client_socket, client_address, ))
            smtp_thread.start()
            
if __name__ == '__main__':
    main() 