from flask import Flask, render_template, jsonify, send_file
import pandas as pd
import io
from datetime import datetime
from aws_service import AWSService

app = Flask(__name__)

# Global variable to store scan results
scan_results = []

@app.route('/')
def index():
    """Serve the main web interface"""
    return render_template('index.html')

@app.route('/api/scan', methods=['POST'])
def scan_aws():
    """Scan all AWS regions for VPC and Subnet information"""
    global scan_results

    try:
        # Initialize AWS service
        aws_service = AWSService()

        # Scan all regions
        result = aws_service.scan_all_regions()

        if result['success']:
            scan_results = result['data']
            return jsonify({
                'success': True,
                'data': scan_results,
                'total_entries': result['total_entries'],
                'regions_scanned': result['regions_scanned']
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error occurred')
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/export', methods=['GET'])
def export_csv():
    """Export scan results to CSV file"""
    global scan_results

    try:
        if not scan_results:
            return jsonify({
                'success': False,
                'error': 'No data available. Please run a scan first.'
            }), 400

        # Create DataFrame
        df = pd.DataFrame(scan_results)

        # Reorder columns to match required format
        df = df[['region', 'vpc_id', 'vpc_name', 'vpc_cidr',
                 'subnet_id', 'subnet_name', 'subnet_cidr']]

        # Rename columns for better readability
        df.columns = ['Region', 'VPC ID', 'VPC Name', 'VPC CIDR',
                      'Subnet ID', 'Subnet Name', 'Subnet CIDR']

        # Create CSV in memory
        output = io.BytesIO()
        df.to_csv(output, index=False, encoding='utf-8')
        output.seek(0)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'aws_vpc_subnet_report_{timestamp}.csv'

        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    print("=" * 60)
    print("AWS VPC and Subnet Information Extraction Tool")
    print("=" * 60)
    print("Starting Flask application...")
    print("Access the application at: http://localhost:5002")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5002)
