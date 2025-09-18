# School Attendance Management System

A modern, comprehensive attendance management system built with Flask and vanilla JavaScript, featuring multiple attendance tracking methods including QR codes, Bluetooth proximity, and AI-powered face recognition.

## Features

### 🎯 Core Functionality
- **Multi-method Attendance**: QR codes, Bluetooth/Wi-Fi proximity, face recognition
- **Role-based Access**: Students, Teachers, and Administrators
- **Real-time Tracking**: Live attendance monitoring and updates
- **Smart Notifications**: Automated alerts for low attendance
- **AI Recommendations**: Personalized study plans and task suggestions

### 👥 User Roles

#### Students
- Secure login with Name + Roll No + Division + Standard
- QR code scanning for attendance
- Personal dashboard with attendance history
- AI-generated study plans and tasks
- Real-time notifications

#### Teachers
- Live attendance monitoring
- QR code generation for classes
- Comprehensive reporting (CSV/PDF export)
- Student engagement analytics
- Class management tools

#### Administrators
- User and permission management
- System-wide reporting and analytics
- Data export capabilities
- System configuration

## Technology Stack

### Backend
- **Flask**: Web framework
- **SQLAlchemy**: Database ORM
- **PostgreSQL**: Primary database (SQLite for development)
- **JWT**: Authentication
- **OpenCV**: Face recognition
- **QRCode**: QR code generation

### Frontend
- **HTML5/CSS3**: Structure and styling
- **Tailwind CSS**: Utility-first CSS framework
- **Vanilla JavaScript**: Client-side functionality
- **Axios**: HTTP client

## Installation & Setup

### Prerequisites
- Python 3.11+
- PostgreSQL (for production) or SQLite (for development)
- Node.js (for frontend dependencies)

### Local Development

1. **Clone the repository**
   \`\`\`bash
   git clone <repository-url>
   cd attendance-system
   \`\`\`

2. **Create virtual environment**
   \`\`\`bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   \`\`\`

3. **Install dependencies**
   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`

4. **Set environment variables**
   \`\`\`bash
   export SECRET_KEY="your-secret-key-here"
   export DATABASE_URL="sqlite:///attendance.db"  # For development
   \`\`\`

5. **Initialize database**
   \`\`\`bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   \`\`\`

6. **Run the application**
   \`\`\`bash
   python app.py
   \`\`\`

### Docker Deployment

1. **Using Docker Compose**
   \`\`\`bash
   docker-compose up --build
   \`\`\`

2. **Access the application**
   - Web interface: http://localhost:5000
   - Database: localhost:5432

### Production Deployment

#### Render/Heroku
1. Set environment variables:
   - `SECRET_KEY`: Strong secret key
   - `DATABASE_URL`: PostgreSQL connection string
   - `FLASK_ENV`: production

2. Deploy using Git or Docker

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/verify` - Token verification

### Attendance
- `POST /api/attendance/generate-qr` - Generate QR code for attendance
- `POST /api/attendance/mark-qr` - Mark attendance via QR code
- `GET /api/attendance/sessions/today` - Get today's sessions
- `GET /api/attendance/report` - Generate attendance reports

## Database Schema

### Key Tables
- **Users**: Base user information
- **Students**: Student-specific data
- **Teachers**: Teacher-specific data
- **Classes**: Class definitions
- **Subjects**: Subject information
- **Timetable**: Class schedules
- **AttendanceSession**: Attendance tracking sessions
- **Attendance**: Individual attendance records
- **Tasks**: AI-generated tasks and assignments
- **Notifications**: System notifications

## Security Features

- **JWT Authentication**: Secure token-based authentication
- **Role-based Access Control**: Granular permissions
- **Data Encryption**: Sensitive data protection
- **Privacy Controls**: GDPR-compliant data handling
- **Secure File Uploads**: Protected file handling

## AI Features

### Face Recognition
- OpenCV-based face detection and recognition
- Privacy-first approach with local processing
- Confidence scoring for accuracy

### Recommendation System
- Personalized study plans based on student interests
- Career goal alignment
- Performance-based task suggestions
- Free period optimization

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Email: support@attendancehub.com
- Documentation: [Wiki](link-to-wiki)
