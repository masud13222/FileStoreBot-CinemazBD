# 📦 Telegram File Sharing Bot

Welcome to the **Telegram File Sharing Bot**, a powerful and smart solution developed by the CinemazBD Team for seamless file sharing. This bot allows users to send files and receive shareable links, along with a suite of other features.

## ✨ Features

- **📤 File Sharing**: Effortlessly send files and receive shareable links.
- **🔄 Batch Operations**: Efficiently manage batch file operations.
- **👥 User Management**: Easily track and manage users.
- **📢 Broadcast Messages**: Communicate with all users through broadcast messages.
- **⚙️ Bot Settings**: Customize bot settings with a user-friendly interface.
- **🗑️ File Deletion**: Securely delete files or messages.
- **🔗 Direct Link Generation**: Create direct links for easy access.
- **🩺 Health Check**: Monitor deployment with integrated health checks.
- **🔗 URL Shortener Support**: Shorten URLs for cleaner links.
- **🔒 Secure and Reliable**: Built with top-notch security and reliability.

## 🚀 Getting Started

### 📋 Prerequisites

- **Python 3.12**: Ensure you have Python installed.
- **Docker**: For containerized deployment.
- **Telegram Bot Token**: Obtain from [BotFather](https://core.telegram.org/bots#botfather).
- **MongoDB Database**: For data storage.

### 🛠️ Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/your-repo-name.git
   cd your-repo-name
   ```

2. **Create a virtual environment and activate it:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**

   Create a `.env` file in the root directory and add your configuration:

   ```
   BOT_TOKEN=your_bot_token_here
   MONGODB_URI=your_mongodb_uri_here
   PREFIX_NAME=@YourChannelName
   PUBLIC_FILES=true
   ADMIN_ID=your_admin_id_here
   SUDO_USERS=
   AUTO_DELETE_TIME=2
   DB_NAME=file_sharing_bot
   WORKER_URL=https://your_worker_url_here
   ```

5. **Run the bot:**

   ```bash
   python main.py
   ```

### 🐳 Docker Deployment

1. **Build the Docker image:**

   ```bash
   docker build -t my-telegram-bot .
   ```

2. **Run the Docker container:**

   ```bash
   docker run -d --name telegram-bot --env-file .env -p 8080:8080 my-telegram-bot
   ```

### ☁️ Koyeb Deployment

1. **Push your code to GitHub.**

2. **Deploy on Koyeb:**

   - Connect your GitHub repository to Koyeb.
   - Set up the build and run commands.
   - Configure environment variables using the `.env.example` as a reference.
   - Deploy the application.

## 📚 Usage

- **Start the bot**: `/start`
- **Batch operations**: `/batch`
- **Get user count**: `/users`
- **Broadcast message**: `/broadcast`
- **Manage settings**: `/bset`
- **Delete file/message**: `/del`
- **Generate direct link**: `/gdirect`

## 🤝 Contributing

Contributions are welcome! Please fork the repository and submit a pull request for any improvements or bug fixes.

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Thanks to the developers of the libraries and tools used in this project.
- Special thanks to the Telegram community for their support and resources.
- Developed by the CinemazBD Team with passion and dedication.

## 📞 Contact

For any inquiries or support, please join our Telegram channel: [@cinemazbd](https://t.me/cinemazbd).