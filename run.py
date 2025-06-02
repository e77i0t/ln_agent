#!/usr/bin/env python3
from app import create_app
import os

def main():
    config_name = os.environ.get('FLASK_ENV', 'development')
    port = int(os.environ.get('PORT', 5280))
    debug = config_name == 'development'
    
    app = create_app(config_name)
    app.run(host='0.0.0.0', port=port, debug=debug)

if __name__ == '__main__':
    main() 