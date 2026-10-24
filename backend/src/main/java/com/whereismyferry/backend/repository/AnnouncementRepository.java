package com.whereismyferry.backend.repository;

import com.whereismyferry.backend.entity.Announcement;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.OffsetDateTime;
import java.util.List;

@Repository
public interface AnnouncementRepository extends JpaRepository<Announcement, Long> {

    @Query("SELECT a FROM Announcement a WHERE a.startsAt <= :now AND (a.endsAt IS NULL OR a.endsAt >= :now) ORDER BY a.startsAt DESC")
    List<Announcement> findActiveAnnouncements(@Param("now") OffsetDateTime now);

    @Query("SELECT a FROM Announcement a WHERE a.startsAt <= :now AND (a.endsAt IS NULL OR a.endsAt >= :now) AND (a.scope = 'ALL' OR (a.scope = :scope AND a.targetId = :targetId)) ORDER BY a.startsAt DESC")
    List<Announcement> findActiveByScopeOrAll(@Param("now") OffsetDateTime now, @Param("scope") String scope, @Param("targetId") String targetId);

    List<Announcement> findByScopeAndTargetId(String scope, String targetId);
}
