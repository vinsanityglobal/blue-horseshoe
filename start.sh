#!/bin/sh
# Blue Horseshoe startup script
# Reads PORT from environment (Railway sets this dynamically)
exec python3 -c "
import os
import uvicorn
port = int(os.environ.get('PORT', 8000))
print(f'Starting Blue Horseshoe on port {port}')
uvicorn.run('main:app', host='0.0.0.0', port=port)
"
