# Refresh PATH to include ffmpeg
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Set location to frontend directory
Set-Location $PSScriptRoot

# Start frontend dev server
npm run dev
