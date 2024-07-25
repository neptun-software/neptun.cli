from pydantic import BaseModel, SecretBytes, SecretStr, field_serializer


class SignUpHttpRequest(BaseModel):
    email: str
    password: SecretStr
    password_bytes: SecretBytes

    @field_serializer('password', 'password_bytes', when_used='json')
    def dump_secret(self, v):
        return v.get_secret_value()


signup_http_request = SignUpHttpRequest(email='test@gmail.com', password='test', password_bytes=b'test')


if __name__ == '__main__':
    print(signup_http_request.model_dump_json())
