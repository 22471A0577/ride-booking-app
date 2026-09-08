\# Security Audit Report



\## 1. Objective



The objective of this security audit was to strengthen authentication,

authorization, API protection, data handling, and abuse prevention

for the ride-booking mobile backend.



\## 2. Authentication



The API uses JWT-based authentication through Django REST Framework

and SimpleJWT.



Security controls reviewed:



\- JWT authentication

\- Access token expiration

\- Refresh token flow

\- Invalid token rejection

\- Authentication before protected API access

\- Separation of authentication and authorization



Authentication flow:



Registration

↓

User Account

↓

Login

↓

Access + Refresh Token

↓

JWT Authentication

↓

Permission Check

↓

API Response



\## 3. Role-Based Authorization



The system defines three user roles:



| Role | Description |

|------|-------------|

| ADMIN | Administrative operations |

| DRIVER | Driver-specific operations |

| USER | Passenger operations |



Custom permission classes were implemented for role-based access:



\- IsAdmin

\- IsAdminOrReadOnly

\- IsAdminOrDriver

\- IsDriver

\- IsRideParticipant



Sensitive driver APIs require the DRIVER role.



\## 4. Object-Level Authorization



Object-level authorization was reviewed for ride and notification

resources.



Security rules include:



\- Passengers can access their own rides.

\- Drivers can access rides assigned to them.

\- Drivers cannot access another driver's ride.

\- Users cannot access another user's notifications.

\- Administrators can access authorized administrative resources.

\- Ride cancellation validates passenger ownership.

\- Ride acceptance validates the authenticated driver's identity.



This prevents horizontal privilege escalation and unauthorized

object access.



\## 5. Sensitive API Protection



Sensitive APIs were reviewed and protected with authentication and

authorization controls.



Protected operations include:



\- Ride acceptance

\- Ride cancellation

\- Driver location updates

\- Ride status updates

\- Fare calculation

\- Nearby driver lookup

\- Notification operations



Driver-specific operations verify the authenticated user's role.



\## 6. API Throttling



DRF throttling was implemented to reduce brute-force attacks,

automated abuse, and excessive requests.



Configured limits:



| API Category | Limit |

|--------------|-------|

| Anonymous requests | 20/minute |

| Authenticated users | 60/minute |

| Login | 5/minute |

| Registration | 3/minute |

| Password reset | 3/minute |

| OTP | 5/minute |

| Ride creation | 10/minute |



Repeated login attempts were verified to return HTTP 429 after the

configured threshold.



\## 7. Secure Data Handling



Serializer output was reviewed for sensitive information.



The API serializers do not expose:



\- User passwords

\- Authentication tokens

\- Secret keys

\- Internal security credentials



Sensitive account fields are not exposed as writable serializer fields.



Email information exposed by response serializers is read-only.



\## 8. Security Testing



Security-focused negative tests were executed to verify authorization

boundaries and protected API behavior.



The tests cover areas including:



\- Authentication requirements

\- Role-based access

\- Object-level authorization

\- Unauthorized ride access

\- Unauthorized ride operations

\- Driver authorization

\- Notification authorization

\- Invalid authentication behavior

\- API throttling



\## 9. Full Test Verification



The complete Django test suite was executed after the security

changes.



Result:



Found 98 test(s)



Ran 98 tests in 120.118s



OK



Therefore, all 98 tests passed successfully.



\## 10. Security Improvements Implemented



The following security improvements were completed:



\- JWT authentication reviewed

\- Role-based permissions implemented

\- Driver-specific permission class added

\- Object-level authorization verified

\- Sensitive APIs protected

\- API throttling implemented

\- Sensitive serializer output reviewed

\- Security negative tests executed

\- Full regression test suite passed



\## 11. Final Status



Security audit status: COMPLETED



Test status: 98/98 PASSED



The backend now has stronger authentication,

authorization, object-level access control, throttling,

and secure data-handling protections suitable for the current

production-readiness stage.

