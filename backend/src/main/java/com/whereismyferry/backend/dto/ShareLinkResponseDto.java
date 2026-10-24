package com.whereismyferry.backend.dto;

import java.time.OffsetDateTime;

public class ShareLinkResponseDto {
    private String token;
    private String shareUrl;
    private String departureCode;
    private OffsetDateTime expiresAt;

    public ShareLinkResponseDto() {}

    public ShareLinkResponseDto(String token, String shareUrl, String departureCode, OffsetDateTime expiresAt) {
        this.token = token;
        this.shareUrl = shareUrl;
        this.departureCode = departureCode;
        this.expiresAt = expiresAt;
    }

    public String getToken() { return token; }
    public void setToken(String token) { this.token = token; }
    public String getShareUrl() { return shareUrl; }
    public void setShareUrl(String shareUrl) { this.shareUrl = shareUrl; }
    public String getDepartureCode() { return departureCode; }
    public void setDepartureCode(String departureCode) { this.departureCode = departureCode; }
    public OffsetDateTime getExpiresAt() { return expiresAt; }
    public void setExpiresAt(OffsetDateTime expiresAt) { this.expiresAt = expiresAt; }
}
