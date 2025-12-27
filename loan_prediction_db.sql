-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Dec 27, 2025 at 09:06 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `loan_prediction_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `predictions`
--

CREATE TABLE `predictions` (
  `id` int(11) NOT NULL,
  `name` varchar(200) DEFAULT NULL,
  `annual_income` float NOT NULL,
  `debt_to_income_ratio` float NOT NULL,
  `credit_score` float NOT NULL,
  `loan_amount` float NOT NULL,
  `interest_rate` float NOT NULL,
  `gender` varchar(50) NOT NULL,
  `marital_status` varchar(50) NOT NULL,
  `education_level` varchar(100) NOT NULL,
  `employment_status` varchar(100) NOT NULL,
  `loan_purpose` varchar(100) NOT NULL,
  `grade_subgrade` varchar(10) NOT NULL,
  `prediction` int(11) NOT NULL,
  `probability` float NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `predictions`
--

INSERT INTO `predictions` (`id`, `name`, `annual_income`, `debt_to_income_ratio`, `credit_score`, `loan_amount`, `interest_rate`, `gender`, `marital_status`, `education_level`, `employment_status`, `loan_purpose`, `grade_subgrade`, `prediction`, `probability`, `created_at`, `user_id`) VALUES
(1, 'Uwineza Eric', 85000, 0.25, 750, 15000, 8.5, 'Male', 'Married', 'Bachelor', 'Employed', 'Home', 'A1', 1, 0.807665, '2025-12-27 07:58:55', 4),
(2, 'Uwineza Eric', 75000, 0.35, 720, 25000, 10.5, 'Male', 'Married', 'Bachelor', 'Employed', 'Home', 'B1', 1, 0.743926, '2025-12-27 07:59:41', 4),
(3, 'Jane Smith', 60000, 0.4, 680, 15000, 12, 'Female', 'Single', 'Master', 'Employed', 'Personal', 'B2', 1, 0.579236, '2025-12-27 07:59:41', 4),
(4, 'Mike Johnson', 90000, 0.25, 750, 30000, 9.5, 'Male', 'Married', 'PhD', 'Employed', 'Auto', 'A1', 1, 0.842572, '2025-12-27 07:59:41', 4),
(5, 'Sarah Williams', 55000, 0.45, 650, 20000, 13.5, 'Female', 'Divorced', 'Bachelor', 'Self-Employed', 'Business', 'C1', 1, 0.509562, '2025-12-27 07:59:41', 4),
(6, 'David Brown', 80000, 0.3, 700, 28000, 11, 'Male', 'Single', 'Master', 'Employed', 'Education', 'B1', 1, 0.715813, '2025-12-27 07:59:41', 4);

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `email` varchar(255) NOT NULL,
  `username` varchar(100) NOT NULL,
  `hashed_password` varchar(255) NOT NULL,
  `full_name` varchar(200) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `is_verified` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `reset_token` varchar(255) DEFAULT NULL,
  `reset_token_expiry` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `email`, `username`, `hashed_password`, `full_name`, `is_active`, `is_verified`, `created_at`, `reset_token`, `reset_token_expiry`) VALUES
(4, 'ericuwinezastarboy@gmail.com', 'Eric', '$2b$12$cP6XJXfLdwpNMLeJ0xwmGO8rDc8xiUC3yE5J3bKyQnCU63L.kcnpG', 'Uwineza Eric', 1, 1, '2025-12-17 06:22:01', 'RQsigY5MWB4uiDqirqEO0VlweHteaCzACFykE0rPHzQ', '2025-12-22 15:02:48');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `predictions`
--
ALTER TABLE `predictions`
  ADD PRIMARY KEY (`id`),
  ADD KEY `ix_predictions_id` (`id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `ix_users_email` (`email`),
  ADD UNIQUE KEY `ix_users_username` (`username`),
  ADD KEY `ix_users_id` (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `predictions`
--
ALTER TABLE `predictions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
