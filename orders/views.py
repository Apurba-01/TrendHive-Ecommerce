from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from carts.models import CartItem
from .forms import OrderForm
import datetime
from .models import Order, Payment, OrderProduct
import json
from store.models import Product
import razorpay
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.shortcuts import render, get_object_or_404
from django.conf import settings



# Create your views here.


def payments(request):
    if request.method == "POST":
        body = json.loads(request.body)

        order = get_object_or_404(Order, user=request.user, is_ordered=False, order_number=body["razorpay_order_id"])

        # Initialize Razorpay Client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        # Verify Payment Signature
        params_dict = {
            'razorpay_order_id': body["razorpay_order_id"],
            'razorpay_payment_id': body["razorpay_payment_id"],
            'razorpay_signature': body["razorpay_signature"]
        }

        try:
            client.utility.verify_payment_signature(params_dict)

            # Save Payment Details
            payment = Payment(
                user=request.user,
                payment_id=body["razorpay_payment_id"],
                payment_method="Razorpay",
                amount_paid=order.order_total,
                status="Completed",
            )
            payment.save()

            # Update Order
            order.payment = payment
            order.is_ordered = True
            order.save()
            
             # Move the cart items to Order Product table
            cart_items = CartItem.objects.filter(user=request.user)

            for item in cart_items:
                orderproduct = OrderProduct()
                orderproduct.order_id = order.id
                orderproduct.payment = payment
                orderproduct.user_id = request.user.id
                orderproduct.product_id = item.product_id
                orderproduct.quantity = item.quantity
                orderproduct.product_price = item.product.price
                orderproduct.ordered = True
                orderproduct.save()

                cart_item = CartItem.objects.get(id=item.id)
                product_variation = cart_item.variations.all()
                orderproduct = OrderProduct.objects.get(id=orderproduct.id)
                orderproduct.variations.set(product_variation)
                orderproduct.save()


                # Reduce the quantity of the sold products
                product = Product.objects.get(id=item.product_id)
                product.stock -= item.quantity
                product.save()

            # Clear cart
            CartItem.objects.filter(user=request.user).delete()

            # Send order recieved email to customer
            mail_subject = 'Thank you for your order!'
            message = render_to_string('orders/order_recieved_email.html', {
                'user': request.user,
                'order': order,
            })
            to_email = request.user.email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            # Send order number and transaction id back to  via JsonResponse
   

            return JsonResponse({
                "success": True,
                "order_number": order.order_number,
                "payment_id": payment.payment_id,
            })
        except razorpay.errors.SignatureVerificationError:
            return JsonResponse({"success": False, "error": "Payment verification failed"}, status=400)

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)



# def payments(request):
#     if request.method == "POST":
#         try:
#             body = json.loads(request.body)
#             order = get_object_or_404(Order, user=request.user, is_ordered=False, order_number=body['orderID'])

#             # Initialize Razorpay client
#             client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

#             # Create a Razorpay order
#             razorpay_order = client.order.create({
#                 "amount": int(order.order_total * 100),  # Amount in paise
#                 "currency": "INR",
#                 "payment_capture": "1"  # Auto-capture
#             })

#             # Store transaction details in the Payment model
#             payment = Payment.objects.create(
#                 user=request.user,
#                 payment_id=razorpay_order['id'],  # Store the Razorpay order ID
#                 payment_method="Razorpay",
#                 amount_paid=order.order_total,
#                 status="Pending",
#             )

#             # Link payment to the order
#             order.payment = payment
#             order.save()

#             return JsonResponse({
#                 "razorpay_order_id": razorpay_order["id"],
#                 "amount": order.order_total * 100,
#                 "currency": "INR",
#                 "key": settings.RAZORPAY_KEY_ID
#             })

#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=400)

#     return render(request, 'orders/payments.html', {"RAZORPAY_KEY_ID": settings.RAZORPAY_KEY_ID})


# def verify_payment(request):
#     """Handles Razorpay payment verification."""
#     if request.method == "POST":
#         try:
#             body = json.loads(request.body)

#             razorpay_payment_id = body.get("razorpay_payment_id")
#             razorpay_order_id = body.get("razorpay_order_id")
#             razorpay_signature = body.get("razorpay_signature")

#             client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

#             # Verify payment signature
#             params_dict = {
#                 "razorpay_payment_id": razorpay_payment_id,
#                 "razorpay_order_id": razorpay_order_id,
#                 "razorpay_signature": razorpay_signature
#             }

#             try:
#                 client.utility.verify_payment_signature(params_dict)
#             except razorpay.errors.SignatureVerificationError:
#                 return JsonResponse({"error": "Invalid payment signature"}, status=400)

#             # Get order and payment details
#             order = get_object_or_404(Order, payment__payment_id=razorpay_order_id)
#             payment = order.payment

#             # Update payment details
#             payment.payment_id = razorpay_payment_id
#             payment.status = "Completed"
#             payment.save()

#             # Mark order as paid
#             order.is_ordered = True
#             order.save()
            
#             # Move the cart items to Order Product table
#             cart_items = CartItem.objects.filter(user=request.user)

#             for item in cart_items:
#                 orderproduct = OrderProduct()
#                 orderproduct.order_id = order.id
#                 orderproduct.payment = payment
#                 orderproduct.user_id = request.user.id
#                 orderproduct.product_id = item.product_id
#                 orderproduct.quantity = item.quantity
#                 orderproduct.product_price = item.product.price
#                 orderproduct.ordered = True
#                 orderproduct.save()

#                 cart_item = CartItem.objects.get(id=item.id)
#                 product_variation = cart_item.variations.all()
#                 orderproduct = OrderProduct.objects.get(id=orderproduct.id)
#                 orderproduct.variations.set(product_variation)
#                 orderproduct.save()


#                 # Reduce the quantity of the sold products
#                 product = Product.objects.get(id=item.product_id)
#                 product.stock -= item.quantity
#                 product.save()

#             # Clear cart
#             CartItem.objects.filter(user=request.user).delete()

#             # Send order recieved email to customer
#             mail_subject = 'Thank you for your order!'
#             message = render_to_string('orders/order_recieved_email.html', {
#                 'user': request.user,
#                 'order': order,
#             })
#             to_email = request.user.email
#             send_email = EmailMessage(mail_subject, message, to=[to_email])
#             send_email.send()

#             # Send order number and transaction id back to sendData method via JsonResponse
#             data = {
#                 'order_number': order.order_number,
#                 'transID': payment.payment_id,
#             }
#             return JsonResponse(data)

#             return JsonResponse({"message": "Payment successful", "order_number": order.order_number})

#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=400)



def place_order(request, total=0, quantity=0,):
    current_user = request.user

    # If the cart count is less than or equal to 0, then redirect back to shop
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')

    grand_total = 0
    tax = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    tax = (18 * total)/100
    grand_total = total + tax

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # Store all the billing information inside Order table
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country'] if 'country' in form.cleaned_data else 'India'  # Fix here  
            data.pincode = form.cleaned_data['pincode']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()
            # Generate order number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr,mt,dt)
            current_date = d.strftime("%Y%m%d") #20210305
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
            }
            return render(request, 'orders/payments.html', context)
            
    else:
        return redirect('checkout')
