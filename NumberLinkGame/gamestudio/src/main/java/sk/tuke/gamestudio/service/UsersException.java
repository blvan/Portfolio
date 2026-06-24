package sk.tuke.gamestudio.service;

public class UsersException extends RuntimeException {
    public UsersException(String message) {
        super(message);
    }

    public UsersException(String message, Throwable cause) {
        super(message, cause);
    }
}

