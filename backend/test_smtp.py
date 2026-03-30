import smtplib
import socket

def test_smtp(host, port, use_ssl):
    print(f"Testing {host}:{port} (SSL: {use_ssl})")
    try:
        if use_ssl:
            conn = smtplib.SMTP_SSL(host, port, timeout=5)
        else:
            conn = smtplib.SMTP(host, port, timeout=5)
            conn.starttls()
        conn.login("muhamusalhassan175@gmail.com", "utiqzyphagqxmpox")
        print("SUCCESS!")
        conn.quit()
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False

# Force IPv4 resolution test
try:
    ipv4 = socket.gethostbyname("smtp.gmail.com")
    print(f"Resolved smtp.gmail.com to IPv4: {ipv4}")
    if test_smtp(ipv4, 587, False):
        print("IPv4 Port 587 works!")
    elif test_smtp(ipv4, 465, True):
        print("IPv4 Port 465 works!")
    else:
        print("Falling back to IPv6/Standard resolution...")
        if test_smtp("smtp.gmail.com", 465, True):
            print("Standard Port 465 overrides the timeout!")
except Exception as e:
    print("Test script error:", e)
