function togglePassword() {
    const passwordField = document.getElementById('password');
    const confirmPasswordField = document.getElementById('confirm_password');
    const newType = passwordField.type === 'password' ? 'text' : 'password';
    passwordField.type = newType;
    confirmPasswordField.type = newType;
}

