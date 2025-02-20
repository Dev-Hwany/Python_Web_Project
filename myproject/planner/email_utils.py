from django.core.mail import get_connection, send_mail


def send_email_dynamic(user, subject, message, recipient_list):
    """
    user: Signup 인스턴스, 여기서 SMTP 설정 정보를 읽어옵니다.
    """
    connection = get_connection(
        backend='django.core.mail.backends.smtp.EmailBackend',
        host=user.smtp_host,
        port=user.smtp_port,
        username=user.smtp_username,
        password=user.smtp_password,
        use_ssl=user.smtp_use_ssl,
    )

    # 발신자 주소는 사용자의 smtp_username을 사용하도록 합니다.
    send_mail(subject, message, user.smtp_username, recipient_list, connection=connection)