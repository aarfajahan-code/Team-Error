-- FoodBridge - Smart Food Redistribution Platform
-- MySQL Database Schema

CREATE DATABASE IF NOT EXISTS `foodbridge` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `foodbridge`;

-- 1. Users Table (Core Auth & Profile)
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(150) NOT NULL,
    `email` VARCHAR(150) UNIQUE NOT NULL,
    `password_hash` VARCHAR(255) NOT NULL,
    `role` ENUM('donor', 'ngo', 'volunteer', 'admin') NOT NULL,
    `phone` VARCHAR(30),
    `address` TEXT,
    `latitude` DECIMAL(10, 8),
    `longitude` DECIMAL(11, 8),
    `status` ENUM('active', 'pending_verification', 'suspended') DEFAULT 'active',
    `avatar_url` VARCHAR(255),
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_role` (`role`),
    INDEX `idx_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Donor Profiles
CREATE TABLE IF NOT EXISTS `donor_profiles` (
    `user_id` INT PRIMARY KEY,
    `organization_name` VARCHAR(150),
    `donor_type` VARCHAR(50) DEFAULT 'Restaurant',
    `contact_person` VARCHAR(100),
    `fssai_license` VARCHAR(50),
    CONSTRAINT `fk_donor_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. NGO Profiles
CREATE TABLE IF NOT EXISTS `ngo_profiles` (
    `user_id` INT PRIMARY KEY,
    `organization_name` VARCHAR(150),
    `registration_no` VARCHAR(100),
    `contact_person` VARCHAR(100),
    `daily_capacity` INT DEFAULT 100,
    `preferred_food_types` VARCHAR(255) DEFAULT 'Vegetarian,Cooked Meal,Raw Groceries',
    `has_cold_storage` TINYINT(1) DEFAULT 0,
    `operating_hours` VARCHAR(100) DEFAULT '08:00 AM - 10:00 PM',
    `verification_status` ENUM('pending', 'verified', 'rejected') DEFAULT 'pending',
    `verified_at` TIMESTAMP NULL,
    CONSTRAINT `fk_ngo_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Volunteer Profiles
CREATE TABLE IF NOT EXISTS `volunteer_profiles` (
    `user_id` INT PRIMARY KEY,
    `vehicle_type` VARCHAR(50) DEFAULT 'Motorbike',
    `max_weight_kg` DECIMAL(6, 2) DEFAULT 25.0,
    `is_available` TINYINT(1) DEFAULT 1,
    `total_deliveries` INT DEFAULT 0,
    `rating` DECIMAL(3, 2) DEFAULT 5.0,
    CONSTRAINT `fk_volunteer_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Donations
CREATE TABLE IF NOT EXISTS `donations` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `donor_id` INT NOT NULL,
    `title` VARCHAR(200) NOT NULL,
    `description` TEXT,
    `category` VARCHAR(50) NOT NULL,
    `food_type` VARCHAR(50) NOT NULL,
    `quantity_value` DECIMAL(8, 2) NOT NULL,
    `quantity_unit` VARCHAR(20) NOT NULL,
    `servings` INT NOT NULL,
    `cooked_at` TIMESTAMP NULL,
    `expiry_time` TIMESTAMP NOT NULL,
    `storage_condition` VARCHAR(100) NOT NULL,
    `pickup_address` TEXT NOT NULL,
    `pickup_lat` DECIMAL(10, 8) NOT NULL,
    `pickup_lng` DECIMAL(11, 8) NOT NULL,
    `special_instructions` TEXT,
    `image_url` TEXT,
    `status` ENUM('available', 'requested', 'confirmed', 'in_transit', 'delivered', 'expired', 'cancelled') DEFAULT 'available',
    `urgency_level` ENUM('low', 'medium', 'critical') DEFAULT 'medium',
    `claimed_by_ngo_id` INT NULL,
    `assigned_volunteer_id` INT NULL,
    `pickup_otp` VARCHAR(10),
    `delivery_otp` VARCHAR(10),
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_donation_status` (`status`),
    INDEX `idx_donation_expiry` (`expiry_time`),
    CONSTRAINT `fk_donation_donor` FOREIGN KEY (`donor_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_donation_ngo` FOREIGN KEY (`claimed_by_ngo_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_donation_volunteer` FOREIGN KEY (`assigned_volunteer_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Claims & Delivery Fulfillment
CREATE TABLE IF NOT EXISTS `claims` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `donation_id` INT NOT NULL,
    `ngo_id` INT NOT NULL,
    `volunteer_id` INT NULL,
    `status` ENUM('pending', 'accepted', 'in_transit', 'completed', 'cancelled') DEFAULT 'accepted',
    `requested_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `accepted_at` TIMESTAMP NULL,
    `picked_up_at` TIMESTAMP NULL,
    `delivered_at` TIMESTAMP NULL,
    `delivery_notes` TEXT,
    `beneficiaries_served` INT DEFAULT 0,
    CONSTRAINT `fk_claim_donation` FOREIGN KEY (`donation_id`) REFERENCES `donations` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_claim_ngo` FOREIGN KEY (`ngo_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_claim_volunteer` FOREIGN KEY (`volunteer_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. Urgency Notifications
CREATE TABLE IF NOT EXISTS `notifications` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `title` VARCHAR(150) NOT NULL,
    `message` TEXT NOT NULL,
    `type` VARCHAR(30) DEFAULT 'info',
    `link` VARCHAR(255),
    `is_read` TINYINT(1) DEFAULT 0,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_notif_user` (`user_id`, `is_read`),
    CONSTRAINT `fk_notif_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. Audit Logs
CREATE TABLE IF NOT EXISTS `audit_logs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NULL,
    `action` VARCHAR(100) NOT NULL,
    `details` TEXT,
    `ip_address` VARCHAR(50),
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_audit_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
