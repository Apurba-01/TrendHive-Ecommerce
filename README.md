
# TrendHive-Ecommerce

**TrendHive-Ecommerce** is a full-stack e-commerce web application developed using Django. It offers a complete online shopping experience, including product browsing, cart management, user authentication, and order processing.

## Features

- **Product Catalog**: Browse a wide range of products categorized for easy navigation.
- **User Authentication**: Secure user registration, login, and profile management.
- **Shopping Cart**: Add, update, or remove products from the shopping cart.
- **Order Management**: Place orders and view order history.
- **Admin Dashboard**: Manage products, categories, orders, and users through an intuitive admin interface.
- **Responsive Design**: Optimized for various devices to ensure a seamless user experience.

## Tech Stack

- **Backend**: Django (Python)
- **Frontend**: HTML, CSS, JavaScript
- **Database**: SQLite (default, can be configured for PostgreSQL or MySQL)
- **Version Control**: Git

## Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/Apurba-01/TrendHive-Ecommerce.git
   cd TrendHive-Ecommerce
   ```

2. **Create a virtual environment**:

   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Apply migrations**:

   ```bash
   python manage.py migrate
   ```

5. **Create a superuser**:

   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**:

   ```bash
   python manage.py runserver
   ```

7. **Access the application**:

   Open your browser and navigate to `http://127.0.0.1:8000/`

## Project Structure

```
TrendHive-Ecommerce/
├── accounts/           # User authentication and profile management
├── carts/              # Shopping cart functionality
├── category/           # Product categories
├── orders/             # Order processing and management
├── store/              # Product listings and details
├── templates/          # HTML templates
├── staticfiles/        # Static assets (CSS, JS, images)
├── media/              # Uploaded media files
├── trendhive/          # Project configuration and settings
├── manage.py           # Django's command-line utility
├── requirements.txt    # Python dependencies
└── db.sqlite3          # SQLite database (default)
```

## Contributing

Contributions are welcome! Please follow these steps:

1. **Fork the repository**.
2. **Create a new branch**:

   ```bash
   git checkout -b feature/YourFeature
   ```

3. **Commit your changes**:

   ```bash
   git commit -m "Add your message here"
   ```

4. **Push to the branch**:

   ```bash
   git push origin feature/YourFeature
   ```

5. **Open a Pull Request**.

## License

This project is licensed under the [MIT License](LICENSE).

## Contact

For any inquiries or feedback, please contact [Apurba-01](https://github.com/Apurba-01).
