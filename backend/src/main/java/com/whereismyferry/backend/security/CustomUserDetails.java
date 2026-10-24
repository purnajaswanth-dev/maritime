package com.whereismyferry.backend.security;

import com.whereismyferry.backend.entity.Role;
import com.whereismyferry.backend.entity.User;
import com.whereismyferry.backend.entity.UserStatus;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;

import java.util.Collection;
import java.util.HashSet;
import java.util.Set;
import java.util.stream.Collectors;

public class CustomUserDetails implements UserDetails {

    private final Long id;
    private final String email;
    private final String password;
    private final boolean enabled;
    private final boolean accountNonLocked;
    private final Collection<? extends GrantedAuthority> authorities;

    public CustomUserDetails(User user) {
        this.id = user.getId();
        this.email = user.getEmail();
        this.password = user.getPasswordHash();
        this.enabled = Boolean.TRUE.equals(user.getEnabled()) && user.getStatus() != UserStatus.SUSPENDED;
        this.accountNonLocked = !user.isAccountLocked();

        Set<GrantedAuthority> auths = new HashSet<>();
        if (user.getRole() != null) {
            auths.add(new SimpleGrantedAuthority("ROLE_" + user.getRole().name()));
        }
        if (user.getRoles() != null) {
            auths.addAll(user.getRoles().stream()
                    .map(role -> new SimpleGrantedAuthority(role.getName()))
                    .collect(Collectors.toSet()));
        }
        this.authorities = auths;
    }

    public Long getId() {
        return id;
    }

    @Override
    public Collection<? extends GrantedAuthority> getAuthorities() {
        return authorities;
    }

    @Override
    public String getPassword() {
        return password;
    }

    @Override
    public String getUsername() {
        return email;
    }

    @Override
    public boolean isAccountNonExpired() {
        return true;
    }

    @Override
    public boolean isAccountNonLocked() {
        return accountNonLocked;
    }

    @Override
    public boolean isCredentialsNonExpired() {
        return true;
    }

    @Override
    public boolean isEnabled() {
        return enabled;
    }
}
