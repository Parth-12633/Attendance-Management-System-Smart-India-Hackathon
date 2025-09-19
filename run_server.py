from app import app
import socket
import qrcode
from io import StringIO

def get_local_ip():
    try:
        # Get the local IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

def create_qr_code(url):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    
    # Create ASCII QR code with basic characters only
    matrix = qr.get_matrix()
    ascii_chars = {
        True: "█",   # Full block for dark modules
        False: " "   # Space for light modules
    }
    
    output = ""
    for row in matrix:
        output += "".join(ascii_chars[cell] for cell in row)
        output += "\n"
    return output

def print_access_info(host, port):
    server_url = f"http://{host}:{port}"
    
    print("\n" + "="*60)
    print("[INFO] Server is running!")
    print("="*60)
    print("\n[ACCESS URLS]")
    print(f"- Local Computer: http://localhost:{port}")
    print(f"- Local Network: {server_url}")
    
    print("\nTo access on mobile devices:")
    print("1. Make sure your mobile device is connected to the same WiFi network")
    print(f"2. Open this URL in your mobile browser: {server_url}")
    try:
        qr = create_qr_code(server_url)
        print("\nQR Code for mobile access:")
        print(qr)
    except Exception as e:
        print("\nNote: QR code display is not supported in this terminal")
    
    print("\n[SECURITY NOTE]")
    print("- This server is accessible to all devices on your local network")
    print("- Do not use this configuration in production")
    
    print("\n[STOP SERVER] Press CTRL+C to stop the server")
    print("="*60 + "\n")

if __name__ == '__main__':
    host = get_local_ip()
    port = 5000
    
    print_access_info(host, port)
    
    # Run the Flask app on all network interfaces
    app.run(host='0.0.0.0', port=port, debug=True)