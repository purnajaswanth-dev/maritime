package com.whereismyferry.backend.repository;

import com.whereismyferry.backend.entity.ShareLink;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.OffsetDateTime;
import java.util.Optional;

@Repository
public interface ShareLinkRepository extends JpaRepository<ShareLink, Long> {
    Optional<ShareLink> findByToken(String token);
    void deleteByExpiresAtBefore(OffsetDateTime now);
}
