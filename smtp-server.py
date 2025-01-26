import threading
import socket
import re
import os 

MAILDIR = "/home/kh4rg0sh/ctfs/Maildir"
HOSTNAME = "kh4rg0sh"
DOMAIN = "lbp.com"
SERVER_IP = "10.81.4.216"
PORT = 25

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
                        error_message = b"503 5.5.1 Error: nested MAIL command \n"
                        client_socket.send(error_message)
            
            elif message[0] == "RCPT" and message[1].startswith("TO:<"):
                print("test RCPT TO") ###

                if not state["MAIL"]:
                    error_message = b"503 5.1.1 Bad sequence of commands \n"
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
                            if recipient_hostname != HOSTNAME:
                                error_message = b"550 5.1.1 Mailbox unavailable \n"
                                client_socket.send(error_message)

                            elif recipient_hostname == HOSTNAME and recipient_domain != DOMAIN:
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

                    print(MAILDIR)
                    if not os.path.isdir(MAILDIR):
                        print("create maildir")
                        os.makedirs(MAILDIR)

                    mail_dir = os.path.expanduser(MAILDIR + "/" + recipient_domain)
                    print(mail_dir)
                    
                    if not os.path.isdir(mail_dir):
                        print("created mail_dir")
                        os.makedirs(mail_dir) 
                    
                    mail_sender = mail_dir + "/" + state["client_hostname"]
                    print(mail_sender)

                    if not os.path.isdir(mail_sender):
                        print("created mail_sender")
                        os.makedirs(mail_sender) 

                    counter = 1
                    while os.path.isfile(f"{mail_sender}/{counter}.txt"):
                        print("created file")
                        counter += 1
                    
                    open_file = open(f"{mail_sender}/{counter}.txt", "w")
                    print(f"{mail_sender}/{counter}.txt")

                    sender = client_socket.recv(1024).decode()
                    sender_mail = sender.strip().lower().split()[-1]

                    recipient = client_socket.recv(1024).decode()
                    recipient_mail = recipient.strip().lower().split()[-1]

                    if recipient_mail != HOSTNAME + "@" + DOMAIN:
                        error_message = b"554 5.7.1 Recipient address rejected: Message header inconsistency"
                        client_socket.send(error_message)
                    
                    elif sender_mail != state["client_hostname"] + "@" + state["client_domain"]:
                        error_message = b"553 5.7.1 Sender address rejected: Policy violation"
                        client_socket.send(error_message)
                    
                    else:
                        open_file.write(sender)
                        open_file.write(recipient)

                        while True:
                            data_message = client_socket.recv(1024).decode()
                            
                            if data_message != ".":
                                open_file.write(data_message)
                                
                            else: 
                                accept_message = b"250 OK: Message accepted \n"
                                client_socket.send(accept_message)

                                open_file.close()
                                break 

                else: 

                    print("handle errors for data") 

            elif message[0] == "QUIT":
                quit_message = b"221 2.0.0 Bye \n"
                client_socket.send(quit_message)
                client_socket.close()

                return 
            
            else:
                error_message = b"500 5.5.2 Syntax error, command unrecognized \n"
                client_socket.send(error_message)

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