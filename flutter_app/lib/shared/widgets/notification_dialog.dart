import 'package:flutter/material.dart';
import '../../config/colors.dart';
import '../../config/typography.dart';

class NotificationDialog extends StatelessWidget {
  final String title;
  final String message;
  final bool isSuccess;
  final VoidCallback? onDismiss;

  const NotificationDialog({
    Key? key,
    required this.title,
    required this.message,
    required this.isSuccess,
    this.onDismiss,
  }) : super(key: key);

  static Future<void> show({
    required BuildContext context,
    required String title,
    required String message,
    required bool isSuccess,
    VoidCallback? onDismiss,
  }) {
    return showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => NotificationDialog(
        title: title,
        message: message,
        isSuccess: isSuccess,
        onDismiss: onDismiss,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      backgroundColor: AppColors.darkSecondary,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(
          color: isSuccess ? AppColors.successGreen : AppColors.errorRed,
          width: 2,
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Icon
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: (isSuccess ? AppColors.successGreen : AppColors.errorRed).withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: Icon(
                isSuccess ? Icons.check_circle : Icons.error,
                color: isSuccess ? AppColors.successGreen : AppColors.errorRed,
                size: 40,
              ),
            ),
            const SizedBox(height: 16),
            
            // Title
            Text(
              title,
              style: AppTypography.labelText.copyWith(
                color: AppColors.cream,
                fontSize: 18,
                fontWeight: FontWeight.w600,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            
            // Message
            Text(
              message,
              style: AppTypography.bodySmall.copyWith(
                color: AppColors.textSecondary,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            
            // OK Button
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () {
                  Navigator.of(context).pop();
                  onDismiss?.call();
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: isSuccess ? AppColors.successGreen : AppColors.gold,
                  foregroundColor: isSuccess ? Colors.white : AppColors.darkPrimary,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
                child: Text(
                  'OK',
                  style: AppTypography.labelText.copyWith(
                    color: isSuccess ? Colors.white : AppColors.darkPrimary,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}