Write-Host "Starting the Financial Assistant..."

# Start backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "
cd '$PSScriptRoot'
.\venv\Scripts\activate
python -m backend.app
"

# Start frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "
cd '$PSScriptRoot\frontend'
npm run dev
"

Write-Host "Backend and frontend launched."