#!/usr/bin/env python3
from app import create_app
import os

def main():
    port = int(os.environ.get('PORT', 5280))
    app = create_app()
    app.run(host='0.0.0.0', port=port, debug=True)

if __name__ == '__main__':
    main() 