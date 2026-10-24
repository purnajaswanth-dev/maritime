package com.whereismyferry.backend.exception;

public class MaintenanceModeException extends RuntimeException {
    public MaintenanceModeException(String message) {
        super(message);
    }
}
