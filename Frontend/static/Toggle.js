function togglePassword() {
    const passwordField = document.getElementById('login-password'); // Get the password input field
    const newType = passwordField.type === 'password' ? 'text' : 'password'; // Toggle between 'password' and 'text'
    passwordField.type = newType; // Set the new type for the password field
}
