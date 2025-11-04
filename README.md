# MamaSHO

A Django-based e-commerce platform for children's clothing. This project provides a full-featured online store with product catalog, shopping basket, user authentication, and admin management capabilities.

## Features

- 🛍️ **Product Catalog**: Browse and search children's clothing products
- 🔍 **Advanced Filtering**: Filter products by category, price range, and availability
- 🛒 **Shopping Basket**: Add, update, and manage items in your shopping basket
- 👤 **User Authentication**: Sign up, login, and logout functionality
- 🔐 **Admin Panel**: Staff and superuser access to manage products
- 📱 **Responsive Design**: Built with Django Tailwind for modern, responsive UI
- ⚡ **HTMX Integration**: Dynamic page updates without full page reloads
- 🖼️ **Image Uploads**: Product image management
- 🔄 **Browser Reload**: Automatic browser reload during development

## Requirements

- Python 3.10 or higher
- Pipenv (for dependency management)
- pip (Python package installer)

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd MamaSHO
```

### 2. Install dependencies

You have two options:

#### Option A: Using Pipenv (Recommended)

If you have an existing Python installation and don't want to install a new version:

```powershell
# Install dependencies using your existing Python
pipenv install

# Or specify Python explicitly (Windows example)
pipenv --python C:\Users\YourUsername\AppData\Local\Programs\Python\Python310\python.exe install
```

#### Option B: Using virtualenv

```bash
# Create a virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
.\venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure environment variables (Optional)

Create a `.env` file in the project root to customize settings:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
```

> **Note**: The project will work with default values if no `.env` file is provided.

### 4. Run database migrations

```bash
# Using Pipenv
pipenv run python manage.py migrate

# Or using activated virtualenv
python manage.py migrate
```

### 5. Create a superuser (Optional)

Create an admin account to access the Django admin panel:

```bash
# Using Pipenv
pipenv run python manage.py createsuperuser

# Or using activated virtualenv
python manage.py createsuperuser
```

Alternatively, you can use the management command:

```bash
pipenv run python manage.py create_admin
```

Or set environment variables for automatic superuser creation:

```env
AUTO_CREATE_SUPERUSER=true
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=your-secure-password
```

Then run migrations again.

## Running the Project

### Development Server

```bash
# Using Pipenv
pipenv shell
python manage.py runserver

# Or without activating shell
pipenv run python manage.py runserver

# Using virtualenv (after activation)
python manage.py runserver
```

The development server will start at `http://127.0.0.1:8000/`

### Access Points

- **Homepage**: `http://127.0.0.1:8000/`
- **Admin Panel**: `http://127.0.0.1:8000/admin/`
- **Login**: `http://127.0.0.1:8000/accounts/login/`
- **Sign Up**: `http://127.0.0.1:8000/accounts/signup/`

## Key Features in Detail

### Product Management

- **View Products**: Browse all products with pagination (15 items per page)
- **Product Details**: View detailed information about each product
- **Search**: Search products by name or category
- **Filtering**: Filter by category, price range, and availability
- **Admin Actions**: Staff members can create, update, and delete products

### Shopping Basket

- **Add to Basket**: Add products with specific quantities
- **Update Quantity**: Modify item quantities in the basket
- **Remove Items**: Remove individual items from the basket
- **Clear Basket**: Empty the entire basket
- **Stock Validation**: Prevents adding more items than available in stock

### User Authentication

- **Registration**: New users can create accounts
- **Login/Logout**: Secure authentication system
- **User Profiles**: Extended customer profiles with contact information
- **Access Control**: Different permissions for regular users, staff, and superusers

## Database

By default, the project uses SQLite (`db.sqlite3`). To use a different database:

1. Set the `DATABASE_URL` environment variable
2. Install the appropriate database adapter (already included for PostgreSQL via `psycopg2-binary`)

Example for PostgreSQL:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/mamasho_db
```

## Technologies Used

- **Django 5.2.7**: Web framework
- **Django Tailwind**: CSS framework integration
- **HTMX**: Dynamic HTML updates
- **WhiteNoise**: Static file serving
- **django-browser-reload**: Automatic browser reload during development
- **Pillow**: Image processing
- **dj-database-url**: Database URL parsing

## Troubleshooting

### Issue: Static files not loading

Collect static files:
```bash
python manage.py collectstatic
```

### Issue: Permission errors

On Windows PowerShell, you might need to allow script execution:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```


## Support

For issues and questions, please open an issue on the GitHub repository.

---

**Note**: This is a development project. For production deployment, ensure you:
- Set `DEBUG=False`
- Configure a production database
- Set up proper static file serving
- Use secure `SECRET_KEY`
- Configure `ALLOWED_HOSTS` appropriately
- Set up HTTPS/SSL