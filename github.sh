#!/bin/bash
# GitHub Application Management Menu for Linux

clear
echo "========================================"
echo "      GitHub Application Manager        "
echo "========================================"
echo

show_menu() {
    echo "Please select an option:"
    echo "1. First time app upload"
    echo "2. App update with code changes"
    echo "3. Exit"
    echo
    read -p "Enter your choice (1-3): " choice

    case $choice in
        1) confirm_first_upload ;;
        2) confirm_app_update ;;
        3) exit_script ;;
        *) 
            echo "Invalid choice. Please try again."
            echo
            show_menu
            ;;
    esac
}

confirm_first_upload() {
    echo
    read -p "Are you sure you want to perform first time app upload? (y/n): " confirm
    case "$confirm" in
        [yY]|[yY][eE][sS]) first_upload ;;
        *) 
            echo "Operation cancelled."
            read -p "Press Enter to continue..."
            show_menu
            ;;
    esac
}

confirm_app_update() {
    echo
    read -p "Are you sure you want to update the app with code changes? (y/n): " confirm
    case "$confirm" in
        [yY]|[yY][eE][sS]) app_update ;;
        *) 
            echo "Operation cancelled."
            read -p "Press Enter to continue..."
            show_menu
            ;;
    esac
}

first_upload() {
    echo
    read -p "Enter GitHub repository URL: " githubpath
    echo
    echo "Initializing Git repository..."
    git init
    echo
    echo "Adding all files..."
    git add .
    echo
    echo "Creating initial commit..."
    git commit -m "Initial commit"
    echo
    echo "Adding remote origin..."
    git remote add origin "$githubpath"
    echo
    echo "Setting main branch..."
    git branch -M main
    echo
    echo "Pushing to GitHub..."
    git push -u origin main
    echo
    echo "First time upload completed!"
    read -p "Press Enter to continue..."
    show_menu
}

app_update() {
    echo
    echo "Adding all files...."
    git add .

    read -p "Describe changes for commit: " commitMessage
    git commit -m "$commitMessage"

    echo "Pushing....."
    git push origin main

    echo "End of process!"
    read -p "Press Enter to continue..."
    show_menu
}

exit_script() {
    echo
    echo "Thank you for using GitHub Application Manager!"
    echo
    exit 0
}

# Start script execution
show_menu