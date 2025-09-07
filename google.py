from gpsoauth import perform_master_login

email = "marcbaumholz07@gmail.com"
app_password = "bkwf qdbc aeve dkqv"
android_id = "0123456789abcdef"  # Fake, aber konsistent

response = perform_master_login(email, app_password, android_id)

if 'Token' in response:
    print("Master Token:", response['Token'])
else:
    print("Fehler beim Login:", response)
