#!/usr/bin/env python3
from app import create_app
import os

def main():
    # Force port 5280
    os.environ['PORT'] = '5280'
    os.environ['FLASK_RUN_PORT'] = '5280'
    
    app = create_app()
    
    # Always use port 5280, ignore any other port settings
    app.run(host='0.0.0.0', port=5280, debug=True)

if __name__ == '__main__':
    main() 