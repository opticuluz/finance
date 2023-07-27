window.addEventListener("load", function() {
  (function($) {
    $(document).ready(function() {
        var paymentTypeField = $('#id_payment_type');
        var targetAccountField = $('#id_targed_account');
        function toggleTargetAccountField() {
            var paymentType = paymentTypeField.val();
            targetAccountField.prop('disabled', paymentType !== 'transfer');
            if (paymentType !== 'transfer') {
              targetAccountField.val('');
            }
        }
        toggleTargetAccountField();
        paymentTypeField.on('change', toggleTargetAccountField);
    });
  })(django.jQuery);
});