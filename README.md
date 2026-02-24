# AWS VPC and Subnet Information Extraction Tool

A lightweight, web-based tool to extract and report VPC and Subnet information from AWS accounts across all regions. Built with Python Flask and modern web technologies.

## Features

- **Multi-Region Scanning**: Automatically scans all AWS regions
- **Comprehensive Data Extraction**: Captures VPC and Subnet details including IDs, names, and CIDR blocks
- **Modern Web Interface**: Bootstrap 5-based responsive UI with dark/light theme
- **CSV Export**: Download scan results in CSV format for reporting and analysis
- **Secure Credentials Management**: AWS credentials stored in config file, not in code
- **Real-time Statistics**: View summary statistics including total entries, unique VPCs, and regions scanned
- **Lightweight**: Minimal dependencies, easy to install and run locally

## Prerequisites

- Python 3.8 or higher
- AWS account with appropriate permissions (EC2 Read access)
- AWS credentials (Access Key ID and Secret Access Key)

## Installation

### 1. Clone or Download the Project

```bash
cd /Users/ramankalia/Documents/AIProjects/Project1
```

### 2. Create a Virtual Environment

```bash
python3 -m venv venv
```

### 3. Activate the Virtual Environment

**On macOS/Linux:**
```bash
source venv/bin/activate
```

**On Windows:**
```bash
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

## Configuration

### First-Time Setup

The application will automatically read AWS credentials from the CSV file located at:
```
Key/deltekDev_aws_dba-cli-user.csv
```

On first run, the application will:
1. Read the AWS credentials from the CSV file
2. Create a `config.ini` file with the credentials
3. Use `config.ini` for subsequent runs

**Important**: The `config.ini` file and `Key/` directory are excluded from version control via `.gitignore` to protect your credentials.

## Usage

### 1. Start the Application

```bash
python app.py
```

You should see output like:
```
============================================================
AWS VPC and Subnet Information Extraction Tool
============================================================
Starting Flask application...
Access the application at: http://localhost:5001
============================================================
 * Running on http://127.0.0.1:5001
 * Running on http://10.10.5.122:5001
```

**Note:** The application runs on port **5001** instead of 5000 to avoid conflicts with macOS AirPlay Receiver which uses port 5000 by default.

### 2. Access the Web Interface

Open your web browser and navigate to:
```
http://localhost:5001
```

### 3. Scan AWS Infrastructure

1. Click the **"Scan AWS Infrastructure"** button
2. Wait for the scan to complete (this may take a few moments depending on the number of regions and resources)
3. View the results in the interactive table

### 4. Export Results

1. After scanning, click the **"Export to CSV"** button
2. The CSV file will be downloaded automatically with a timestamp in the filename

## CSV Report Format

The generated CSV report includes the following columns:

| Column | Description |
|--------|-------------|
| Region | AWS region name (e.g., us-east-1) |
| VPC ID | VPC identifier |
| VPC Name | VPC name from tags (if available) |
| VPC CIDR | VPC CIDR block |
| Subnet ID | Subnet identifier |
| Subnet Name | Subnet name from tags (if available) |
| Subnet CIDR | Subnet CIDR block |

### Sample CSV Output:

```csv
Region,VPC ID,VPC Name,VPC CIDR,Subnet ID,Subnet Name,Subnet CIDR
us-east-1,vpc-0a1b2c3d4e5f6g7h8,Production VPC,10.0.0.0/16,subnet-0x1y2z3a4b5c6d7e8,Public Subnet 1A,10.0.1.0/24
us-east-1,vpc-0a1b2c3d4e5f6g7h8,Production VPC,10.0.0.0/16,subnet-0x1y2z3a4b5c6d7e9,Private Subnet 1A,10.0.2.0/24
us-west-2,vpc-1a2b3c4d5e6f7g8h9,Staging VPC,192.168.0.0/16,subnet-1x2y3z4a5b6c7d8e9,Staging Subnet,192.168.1.0/24
```

## Project Structure

```
Project1/
├── app.py                      # Main Flask application
├── aws_service.py              # AWS API interactions using boto3
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
├── .gitignore                  # Exclude credentials and sensitive files
├── config.ini                  # Configuration file (auto-generated)
├── README.md                   # Installation and usage instructions
├── templates/
│   └── index.html             # Main web interface
├── static/
│   ├── css/
│   │   └── style.css          # Custom styles
│   └── js/
│       └── app.js             # Frontend JavaScript
└── Key/
    └── deltekDev_aws_dba-cli-user.csv  # AWS credentials (excluded from git)
```

## Security Considerations

- **Credentials Protection**: AWS credentials are never hardcoded in the application
- **Git Exclusion**: Sensitive files (`config.ini`, `Key/` directory, `*.csv`) are excluded from version control
- **Local Installation**: Application runs locally on your machine, no data sent to external servers
- **Read-Only Access**: Application only requires EC2 read permissions to scan VPC and Subnet information

## Troubleshooting

### Issue: "Neither config.ini nor Key/deltekDev_aws_dba-cli-user.csv found"

**Solution**: Ensure the AWS credentials CSV file exists at `Key/deltekDev_aws_dba-cli-user.csv`

### Issue: "AWS credentials not found or invalid"

**Solution**:
1. Verify your AWS credentials are correct
2. Delete `config.ini` and restart the application to regenerate it from the CSV file
3. Ensure your AWS credentials have the necessary permissions (EC2 Read access)

### Issue: "Skipping region {region}: Unauthorized"

**Solution**: This is normal for regions where your AWS account doesn't have access. The application will skip these regions and continue scanning others.

### Issue: Port 5001 already in use

**Solution**: Either stop the process using port 5001 or modify the port in `app.py` line 106:
```python
app.run(debug=True, host='0.0.0.0', port=5002)  # Change to any available port
```

### Issue: Port 5000 conflict with AirPlay Receiver (macOS)

**Solution**: The application has been configured to use port 5001 by default to avoid this conflict. If you still experience issues:
- Disable AirPlay Receiver in System Settings > General > AirDrop & Handoff
- Or use a different port (see above)

### Issue: Application not starting

**Solution**:
1. Ensure virtual environment is activated: `source venv/bin/activate`
2. Ensure dependencies are installed: `pip install -r requirements.txt`
3. Check Python version: `python --version` (should be 3.8+)

## Stopping the Application

### From Terminal (if running in foreground):
Press `Ctrl + C`

### If Running in Background:
```bash
pkill -f "python app.py"
```

### Check if Application is Running:
```bash
ps aux | grep "python app.py"
```

Or check port usage:
```bash
lsof -i :5001
```

## AWS Permissions Required

The AWS credentials must have at least the following permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeRegions",
                "ec2:DescribeVpcs",
                "ec2:DescribeSubnets"
            ],
            "Resource": "*"
        }
    ]
}
```

## Technology Stack

- **Backend**: Python 3, Flask
- **AWS SDK**: boto3
- **Data Processing**: pandas
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **UI Framework**: Bootstrap 5
- **Icons**: Bootstrap Icons

## Quick Start Summary

```bash
# 1. Navigate to project directory
cd /Users/ramankalia/Documents/AIProjects/Project1

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run application
python app.py

# 5. Access in browser
open http://localhost:5001
```

## Features Roadmap

- [ ] Filter results by region
- [ ] Search functionality in results table
- [ ] Export to additional formats (Excel, JSON)
- [ ] Support for multiple AWS accounts
- [ ] Scheduled scans
- [ ] Historical data comparison

## Support

For issues, questions, or contributions, please contact the development team.

## License

Internal use only - Not for public distribution.

---

**Last Updated**: February 2026
**Application Port**: 5001
**Status**: Production Ready
