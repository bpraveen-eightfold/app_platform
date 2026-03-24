# Import matplotlib
import time
import traceback

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.offsetbox import AnnotationBbox
import random

from matplotlib.projections import PolarAxes
from matplotlib.patches import Circle, RegularPolygon
from matplotlib.spines import Spine
from matplotlib.transforms import Affine2D
from matplotlib.projections import register_projection
from matplotlib.path import Path

import pandas as pd
import skunk
import base64
import io
import json
import xml.etree.ElementTree as ET

ET.register_namespace("", "http://www.w3.org/2000/svg")

service_svg = '<svg style="width:100%" viewBox="0 0 83 83" fill="none" xmlns="http://www.w3.org/2000/svg">'
service_svg = (
        service_svg
        + '<path d="M27.7734 48.3242L37.9159 48.3256" stroke="black" stroke-width="1.52323" stroke-linecap="round" stroke-linejoin="round"/>'
)
service_svg = (
        service_svg
        + '<path d="M28.5938 32.3164H53.9198" stroke="black" stroke-width="1.52323" stroke-linecap="round" stroke-linejoin="round"/>'
)
service_svg = (
        service_svg
        + '<path d="M39.2499 40.3216L25.9219 40.3203" stroke="black" stroke-width="1.52323" stroke-linecap="round" stroke-linejoin="round"/>'
)
service_svg = (
        service_svg
        + '<path d="M40.4199 56.3072C37.5115 56.1468 34.709 55.1617 32.3399 53.4672C29.9708 51.7726 28.1331 49.4387 27.0416 46.7382C25.9502 44.0377 25.65 41.0822 26.1764 38.2174C26.7027 35.3526 28.0337 32.6969 30.0137 30.5607C31.9938 28.4245 34.5411 26.8961 37.3578 26.1543C40.1745 25.4125 43.1442 25.4879 45.9196 26.3716C48.695 27.2554 51.1615 28.911 53.0306 31.1449C54.8997 33.3789 56.0943 36.0987 56.4746 38.9865" stroke="black" stroke-width="1.52323" stroke-linecap="round" stroke-linejoin="round"/>'
)
service_svg = (
        service_svg
        + '<path d="M40.2746 25.6836C32.2705 34.3546 32.4159 45.6376 40.42 56.3096" stroke="black" stroke-width="1.52323" stroke-linecap="round" stroke-linejoin="round"/>'
)
service_svg = (
        service_svg
        + '<path d="M42.2227 25.6836C45.7038 29.2796 47.7952 33.9948 48.1243 38.9889" stroke="black" stroke-width="1.52323" stroke-linecap="round" stroke-linejoin="round"/>'
)
service_svg = (
        service_svg
        + '<path d="M48.5865 56.3264L41.7644 49.2095C41.1653 48.6106 40.77 47.8385 40.6342 47.0024C40.4984 46.1663 40.6292 45.3088 41.008 44.5511V44.5511C41.2941 43.9791 41.712 43.4833 42.2273 43.1045C42.7427 42.7257 43.3406 42.4748 43.9719 42.3724C44.6032 42.27 45.2498 42.3191 45.8585 42.5156C46.4671 42.7121 47.0203 43.0504 47.4726 43.5026L48.5865 44.6165L49.7003 43.5026C50.1526 43.0504 50.7058 42.7121 51.3144 42.5156C51.9231 42.3191 52.5697 42.27 53.201 42.3724C53.8323 42.4748 54.4302 42.7257 54.9456 43.1045C55.4609 43.4833 55.8788 43.9791 56.1649 44.5511V44.5511C56.5437 45.3088 56.6745 46.1663 56.5387 47.0024C56.403 47.8385 56.0076 48.6106 55.4085 49.2095L48.5865 56.3264Z" stroke="black" stroke-width="1.52323" stroke-linecap="round" stroke-linejoin="round"/>'
)
service_svg = (
        service_svg
        + '<circle cx="41.2557" cy="40.9862" r="39.4862" stroke="#C53E97" stroke-width="3"/>'
)
service_svg = service_svg + "</svg>"

cohesion_svg = '<svg style="width:100%" viewBox="0 0 83 83" fill="none" xmlns="http://www.w3.org/2000/svg">'
cohesion_svg = (
        cohesion_svg
        + '<path d="M31.2898 38.9858C33.1315 38.9858 34.6245 37.4928 34.6245 35.6511C34.6245 33.8094 33.1315 32.3164 31.2898 32.3164C29.4481 32.3164 27.9551 33.8094 27.9551 35.6511C27.9551 37.4928 29.4481 38.9858 31.2898 38.9858Z" stroke="black" stroke-width="1.45405" stroke-linecap="round" stroke-linejoin="round"/>'
)
cohesion_svg = (
        cohesion_svg
        + '<path d="M52.6316 38.9858C54.4733 38.9858 55.9663 37.4928 55.9663 35.6511C55.9663 33.8094 54.4733 32.3164 52.6316 32.3164C50.7899 32.3164 49.2969 33.8094 49.2969 35.6511C49.2969 37.4928 50.7899 38.9858 52.6316 38.9858Z" stroke="black" stroke-width="1.45405" stroke-linecap="round" stroke-linejoin="round"/>'
)
cohesion_svg = (
        cohesion_svg
        + '<path d="M47.9637 56.3291V45.6207C46.2885 45.4659 44.6946 44.8264 43.377 43.7803C42.0594 42.7342 41.0752 41.3268 40.5447 39.7303L39.3962 36.2875C39.3039 36.0113 39.2729 35.7183 39.3056 35.4289C39.3382 35.1395 39.4336 34.8607 39.5851 34.612C39.7367 34.3633 39.9407 34.1506 40.1829 33.9889C40.4251 33.8272 40.6997 33.7204 40.9876 33.6758C41.4709 33.6162 41.9599 33.7282 42.3692 33.9922C42.7785 34.2562 43.0821 34.6554 43.2271 35.1204L44.3423 38.4644C44.6518 39.3928 45.2452 40.2004 46.0386 40.7732C46.8321 41.3459 47.7855 41.6549 48.7641 41.6564H54.6251C55.3327 41.6564 56.0112 41.9375 56.5115 42.4378C57.0118 42.9381 57.2929 43.6166 57.2929 44.3241V56.3291" stroke="black" stroke-width="1.45405" stroke-linecap="round" stroke-linejoin="round"/>'
)
cohesion_svg = (
        cohesion_svg
        + '<path d="M39.8511 37.6523L39.5844 38.462C39.274 39.393 38.6781 40.2024 37.8815 40.7754C37.0848 41.3485 36.1279 41.6559 35.1465 41.654H29.2908C28.5833 41.654 27.9047 41.9351 27.4044 42.4354C26.9041 42.9357 26.623 43.6142 26.623 44.3217V56.3267" stroke="black" stroke-width="1.45405" stroke-linecap="round" stroke-linejoin="round"/>'
)
cohesion_svg = (
        cohesion_svg
        + '<path d="M35.957 56.3291V45.6207C37.1264 45.5126 38.2616 45.1677 39.2935 44.607C40.3254 44.0464 41.2325 43.2817 41.9595 42.3594" stroke="black" stroke-width="1.45405" stroke-linecap="round" stroke-linejoin="round"/>'
)
cohesion_svg = (
        cohesion_svg
        + '<path d="M41.293 25.6484V28.3162" stroke="black" stroke-width="1.45405" stroke-linecap="round" stroke-linejoin="round"/>'
)
cohesion_svg = (
        cohesion_svg
        + '<path d="M46.515 28.4297L44.6289 30.3158" stroke="black" stroke-width="1.45405" stroke-linecap="round" stroke-linejoin="round"/>'
)
cohesion_svg = (
        cohesion_svg
        + '<path d="M36.0723 28.4297L37.9584 30.3158" stroke="black" stroke-width="1.45405" stroke-linecap="round" stroke-linejoin="round"/>'
)
cohesion_svg = (
        cohesion_svg
        + '<circle cx="41.9569" cy="40.9862" r="39.4862" stroke="#C53E97" stroke-width="3"/>'
)
cohesion_svg = cohesion_svg + "</svg>"

quality_svg = '<svg style="width:100%" viewBox="0 0 83 83" fill="none" xmlns="http://www.w3.org/2000/svg">'
quality_svg = quality_svg + '<g clip-path="url(#clip0_226_207)">'
quality_svg = (
        quality_svg
        + '<path d="M46.0777 49.2617V55.0156C46.0777 55.7065 45.6782 55.8723 45.1895 55.3836L41.0525 51.2467L36.9155 55.3836C36.4268 55.8723 36.0273 55.7065 36.0273 55.5445V49.263" stroke="black" stroke-width="1.25629" stroke-linecap="round" stroke-linejoin="round"/>'
)
quality_svg = (
        quality_svg
        + '<path d="M40.7718 33.8021C40.9263 33.4931 41.1789 33.4931 41.3334 33.8021L42.5168 36.1715H44.8221C45.1676 36.1715 45.2229 36.3398 44.9477 36.5484L43.0055 37.983L43.8058 40.7268C43.9025 41.0585 43.743 41.1778 43.4528 40.9919L41.0532 39.4605L38.6537 40.9441C38.3597 41.1263 38.2002 41.0057 38.2994 40.6728L39.0984 37.9906L37.1587 36.5471C36.8811 36.3411 36.9376 36.1702 37.2843 36.1702H39.5871L40.7718 33.8021Z" stroke="black" stroke-width="1.25629" stroke-linecap="round" stroke-linejoin="round"/>'
)
quality_svg = (
        quality_svg
        + '<path d="M31.002 37.4293C31.002 40.0948 32.0608 42.6511 33.9456 44.5359C35.8304 46.4208 38.3868 47.4796 41.0523 47.4796C43.7178 47.4796 46.2742 46.4208 48.159 44.5359C50.0438 42.6511 51.1027 40.0948 51.1027 37.4293C51.1027 34.7637 50.0438 32.2074 48.159 30.3226C46.2742 28.4378 43.7178 27.3789 41.0523 27.3789C38.3868 27.3789 35.8304 28.4378 33.9456 30.3226C32.0608 32.2074 31.002 34.7637 31.002 37.4293V37.4293Z" stroke="black" stroke-width="1.25629" stroke-linecap="round" stroke-linejoin="round"/>'
)
quality_svg = (
        quality_svg
        + '<path d="M34.1426 37.4292C34.1426 39.2617 34.8706 41.0192 36.1664 42.315C37.4622 43.6108 39.2197 44.3388 41.0522 44.3388C42.8847 44.3388 44.6422 43.6108 45.938 42.315C47.2338 41.0192 47.9618 39.2617 47.9618 37.4292C47.9618 35.5966 47.2338 33.8391 45.938 32.5433C44.6422 31.2475 42.8847 30.5195 41.0522 30.5195C39.2197 30.5195 37.4622 31.2475 36.1664 32.5433C34.8706 33.8391 34.1426 35.5966 34.1426 37.4292V37.4292Z" stroke="black" stroke-width="1.25629" stroke-linecap="round" stroke-linejoin="round"/>'
)
quality_svg = quality_svg + "</g>"
quality_svg = (
        quality_svg
        + '<circle cx="41.0526" cy="41.5448" r="39.4862" stroke="#f47862" stroke-width="3"/>'
)
quality_svg = quality_svg + "<defs>"
quality_svg = quality_svg + '<clipPath id="clip0_226_207">'
quality_svg = (
        quality_svg
        + '<rect width="30.1511" height="30.1511" fill="white" transform="translate(25.9766 26.4688)"/>'
)
quality_svg = quality_svg + "</clipPath>"
quality_svg = quality_svg + "</defs>"
quality_svg = quality_svg + "</svg>"

certainty_svg = '<svg style="width:100%" viewBox="0 0 83 83" fill="none" xmlns="http://www.w3.org/2000/svg">'
certainty_svg = certainty_svg + '<g clip-path="url(#clip0_226_208)">'
certainty_svg = (
        certainty_svg
        + '<path d="M26.6758 48.352C26.6758 50.0326 27.3434 51.6443 28.5317 52.8326C29.72 54.0209 31.3317 54.6885 33.0122 54.6885C34.6927 54.6885 36.3044 54.0209 37.4927 52.8326C38.681 51.6443 39.3486 50.0326 39.3486 48.352C39.3486 46.6715 38.681 45.0598 37.4927 43.8715C36.3044 42.6832 34.6927 42.0156 33.0122 42.0156C31.3317 42.0156 29.72 42.6832 28.5317 43.8715C27.3434 45.0598 26.6758 46.6715 26.6758 48.352V48.352Z" stroke="black" stroke-width="1.26728" stroke-linecap="round" stroke-linejoin="round"/>'
)
certainty_svg = (
        certainty_svg
        + '<path d="M39.3489 33.7782V28.709C38.8223 28.2494 38.147 27.9961 37.448 27.9961C36.749 27.9961 36.0737 28.2494 35.5471 28.709L33.6461 33.7782L31.7452 35.6791L27.9434 44.5501" stroke="black" stroke-width="1.26728" stroke-linecap="round" stroke-linejoin="round"/>'
)
certainty_svg = (
        certainty_svg
        + '<path d="M43.1504 48.352C43.1504 50.0326 43.818 51.6443 45.0063 52.8326C46.1946 54.0209 47.8063 54.6885 49.4868 54.6885C51.1673 54.6885 52.779 54.0209 53.9673 52.8326C55.1556 51.6443 55.8232 50.0326 55.8232 48.352C55.8232 46.6715 55.1556 45.0598 53.9673 43.8715C52.779 42.6832 51.1673 42.0156 49.4868 42.0156C47.8063 42.0156 46.1946 42.6832 45.0063 43.8715C43.818 45.0598 43.1504 46.6715 43.1504 48.352V48.352Z" stroke="black" stroke-width="1.26728" stroke-linecap="round" stroke-linejoin="round"/>'
)
certainty_svg = (
        certainty_svg
        + '<path d="M43.1504 33.7765V28.7872C43.677 28.3275 44.3523 28.0742 45.0513 28.0742C45.7503 28.0742 46.4256 28.3275 46.9522 28.7872L48.8532 33.7765L50.7541 35.6774L54.5559 44.5484" stroke="black" stroke-width="1.26728" stroke-linecap="round" stroke-linejoin="round"/>'
)
certainty_svg = (
        certainty_svg
        + '<path d="M36.1797 38.8471C36.1797 37.4531 38.4494 36.3125 41.2488 36.3125C44.0482 36.3125 46.318 37.4467 46.318 38.8471" stroke="black" stroke-width="1.26728" stroke-linecap="round" stroke-linejoin="round"/>'
)
certainty_svg = (
        certainty_svg
        + '<path d="M39.3477 48.3515V36.4961" stroke="black" stroke-width="1.26728" stroke-linecap="round" stroke-linejoin="round"/>'
)
certainty_svg = (
        certainty_svg
        + '<path d="M43.1504 48.3515V36.4961" stroke="black" stroke-width="1.26728" stroke-linecap="round" stroke-linejoin="round"/>'
)
certainty_svg = certainty_svg + "</g>"
certainty_svg = (
        certainty_svg
        + '<circle cx="41.2499" cy="41.3417" r="39.4862" stroke="#f47862" stroke-width="3"/>'
)
certainty_svg = certainty_svg + "<defs>"
certainty_svg = certainty_svg + '<clipPath id="clip0_226_208">'
certainty_svg = (
        certainty_svg
        + '<rect width="30.4148" height="30.4148" fill="white" transform="translate(27 26.1328)"/>'
)
certainty_svg = certainty_svg + "</clipPath>"
certainty_svg = certainty_svg + "</defs>"
certainty_svg = certainty_svg + "</svg>"

legacy_svg = '<svg style="width:100%" viewBox="0 0 83 83" fill="none" xmlns="http://www.w3.org/2000/svg">'
legacy_svg = legacy_svg + '<g clip-path="url(#clip0_226_209)">'
legacy_svg = (
        legacy_svg
        + '<path d="M38.6445 29.3298C38.6445 30.0005 38.911 30.6438 39.3853 31.1181C39.8595 31.5924 40.5028 31.8588 41.1735 31.8588C41.8443 31.8588 42.4875 31.5924 42.9618 31.1181C43.4361 30.6438 43.7026 30.0005 43.7026 29.3298C43.7026 28.6591 43.4361 28.0158 42.9618 27.5415C42.4875 27.0672 41.8443 26.8008 41.1735 26.8008C40.5028 26.8008 39.8595 27.0672 39.3853 27.5415C38.911 28.0158 38.6445 28.6591 38.6445 29.3298V29.3298Z" stroke="black" stroke-width="1.2645" stroke-linecap="round" stroke-linejoin="round"/>'
)
legacy_svg = (
        legacy_svg
        + '<path d="M49.3918 47.6663L51.3517 45.7063C51.3977 45.6602 51.4568 45.6294 51.5209 45.6181C51.585 45.6068 51.6511 45.6156 51.71 45.6432C51.769 45.6709 51.818 45.7161 51.8502 45.7727C51.8825 45.8292 51.8966 45.8944 51.8904 45.9592C51.6868 48.6624 50.4693 51.1889 48.4817 53.0325C46.4942 54.876 43.8834 55.9004 41.1725 55.9004C38.4616 55.9004 35.8508 54.876 33.8632 53.0325C31.8756 51.1889 30.6581 48.6624 30.4545 45.9592C30.4484 45.8944 30.4624 45.8292 30.4947 45.7727C30.527 45.7161 30.576 45.6709 30.6349 45.6432C30.6939 45.6156 30.7599 45.6068 30.824 45.6181C30.8882 45.6294 30.9473 45.6602 30.9932 45.7063L32.9532 47.6663" stroke="black" stroke-width="1.2645" stroke-linecap="round" stroke-linejoin="round"/>'
)
legacy_svg = (
        legacy_svg
        + '<path d="M41.1738 31.8594V55.885" stroke="black" stroke-width="1.2645" stroke-linecap="round" stroke-linejoin="round"/>'
)
legacy_svg = (
        legacy_svg
        + '<path d="M35.4824 38.1797H46.863" stroke="black" stroke-width="1.2645" stroke-linecap="round" stroke-linejoin="round"/>'
)
legacy_svg = legacy_svg + "</g>"
legacy_svg = (
        legacy_svg
        + '<circle cx="41.1737" cy="41.3417" r="39.4862" stroke="#f47862" stroke-width="3"/>'
)
legacy_svg = legacy_svg + "<defs>"
legacy_svg = legacy_svg + '<clipPath id="clip0_226_209">'
legacy_svg = (
        legacy_svg
        + '<rect width="30.3481" height="30.3481" fill="white" transform="translate(26 26.168)"/>'
)
legacy_svg = legacy_svg + "</clipPath>"
legacy_svg = legacy_svg + "</defs>"
legacy_svg = legacy_svg + "</svg>"

authority_svg = '<svg style="width:100%" viewBox="0 0 83 83" fill="none" xmlns="http://www.w3.org/2000/svg">'
authority_svg = authority_svg + '<g clip-path="url(#clip0_226_205)">'
authority_svg = (
        authority_svg
        + '<path d="M41.9626 45.8354C44.6559 45.8354 46.8393 43.652 46.8393 40.9587C46.8393 38.2654 44.6559 36.082 41.9626 36.082C39.2693 36.082 37.0859 38.2654 37.0859 40.9587C37.0859 43.652 39.2693 45.8354 41.9626 45.8354Z" stroke="black" stroke-width="1.39333" stroke-linecap="round" stroke-linejoin="round"/>'
)
authority_svg = (
        authority_svg
        + '<path d="M41.963 43.0511C43.1173 43.0511 44.053 42.1154 44.053 40.9611C44.053 39.8068 43.1173 38.8711 41.963 38.8711C40.8088 38.8711 39.873 39.8068 39.873 40.9611C39.873 42.1154 40.8088 43.0511 41.963 43.0511Z" stroke="black" stroke-width="1.39333" stroke-linecap="round" stroke-linejoin="round"/>'
)
authority_svg = (
        authority_svg
        + '<path d="M41.9625 52.8038C48.5033 52.8038 53.8058 47.5014 53.8058 40.9605C53.8058 34.4196 48.5033 29.1172 41.9625 29.1172C35.4216 29.1172 30.1191 34.4196 30.1191 40.9605C30.1191 47.5014 35.4216 52.8038 41.9625 52.8038Z" stroke="black" stroke-width="1.39333" stroke-linecap="round" stroke-linejoin="round"/>'
)
authority_svg = (
        authority_svg
        + '<path d="M41.9629 45.8359V56.3417" stroke="black" stroke-width="1.39333" stroke-linecap="round" stroke-linejoin="round"/>'
)
authority_svg = (
        authority_svg
        + '<path d="M41.9629 25.6602V36.0823" stroke="black" stroke-width="1.39333" stroke-linecap="round" stroke-linejoin="round"/>'
)
authority_svg = (
        authority_svg
        + '<path d="M38.5358 44.4297L31.1094 51.8561" stroke="black" stroke-width="1.39333" stroke-linecap="round" stroke-linejoin="round"/>'
)
authority_svg = (
        authority_svg
        + '<path d="M52.8183 30.1602L45.4336 37.5309" stroke="black" stroke-width="1.39333" stroke-linecap="round" stroke-linejoin="round"/>'
)
authority_svg = (
        authority_svg
        + '<path d="M38.494 37.5309L31.1094 30.1602" stroke="black" stroke-width="1.39333" stroke-linecap="round" stroke-linejoin="round"/>'
)
authority_svg = (
        authority_svg
        + '<path d="M52.8171 51.8561L45.3906 44.4297" stroke="black" stroke-width="1.39333" stroke-linecap="round" stroke-linejoin="round"/>'
)
authority_svg = (
        authority_svg
        + '<path d="M37.0867 40.9609H26.6367" stroke="black" stroke-width="1.39333" stroke-linecap="round" stroke-linejoin="round"/>'
)
authority_svg = (
        authority_svg
        + '<path d="M57.3177 40.9609H46.8398" stroke="black" stroke-width="1.39333" stroke-linecap="round" stroke-linejoin="round"/>'
)
authority_svg = authority_svg + "</g>"
authority_svg = (
        authority_svg
        + '<circle cx="41.9764" cy="41.0018" r="39.4862" stroke="#5ac6cd" stroke-width="3"/>'
)
authority_svg = authority_svg + "<defs>"
authority_svg = authority_svg + '<clipPath id="clip0_226_205">'
authority_svg = (
        authority_svg
        + '<rect width="33.44" height="33.44" fill="white" transform="translate(25.2559 24.2812)"/>'
)
authority_svg = authority_svg + "</clipPath>"
authority_svg = authority_svg + "</defs>"
authority_svg = authority_svg + "</svg>"

competition_svg = '<svg style="width:100%" viewBox="0 0 83 83" fill="none" xmlns="http://www.w3.org/2000/svg">'
competition_svg = competition_svg + '<g clip-path="url(#clip0_226_206)">'
competition_svg = (
        competition_svg
        + '<path d="M30.1865 38.3596C29.2169 38.0011 28.3804 37.3541 27.7897 36.5057C27.199 35.6574 26.8825 34.6483 26.8828 33.6146V32.3503C26.8828 32.0149 27.016 31.6934 27.2531 31.4562C27.4902 31.2191 27.8118 31.0859 28.1471 31.0859H32.3194" stroke="black" stroke-width="1.26432" stroke-linecap="round" stroke-linejoin="round"/>'
)
competition_svg = (
        competition_svg
        + '<path d="M52.6583 38.3596C53.6279 38.0011 54.4644 37.3541 55.0551 36.5057C55.6458 35.6574 55.9623 34.6483 55.962 33.6146V32.3503C55.962 32.0149 55.8288 31.6934 55.5917 31.4562C55.3546 31.2191 55.033 31.0859 54.6977 31.0859H50.5254" stroke="black" stroke-width="1.26432" stroke-linecap="round" stroke-linejoin="round"/>'
)
competition_svg = (
        competition_svg
        + '<path d="M42.0268 30.8172L43.3265 33.6152H45.8552C45.9829 33.6096 46.1091 33.6438 46.2166 33.713C46.3241 33.7822 46.4075 33.883 46.4553 34.0015C46.5032 34.12 46.5131 34.2505 46.4837 34.3749C46.4543 34.4993 46.3871 34.6115 46.2913 34.6962L44.0965 36.8582L45.3128 39.651C45.366 39.779 45.3778 39.9203 45.3465 40.0553C45.3152 40.1903 45.2423 40.312 45.1382 40.4034C45.0341 40.4948 44.904 40.5513 44.7661 40.5649C44.6282 40.5785 44.4895 40.5485 44.3696 40.4792L41.4313 38.8267L38.493 40.4792C38.3731 40.5485 38.2344 40.5785 38.0965 40.5649C37.9586 40.5513 37.8285 40.4948 37.7244 40.4034C37.6203 40.312 37.5474 40.1903 37.5161 40.0553C37.4848 39.9203 37.4966 39.779 37.5498 39.651L38.7661 36.8582L36.5712 34.6987C36.4746 34.6144 36.4065 34.502 36.3765 34.3773C36.3465 34.2525 36.3561 34.1215 36.4039 34.0025C36.4517 33.8834 36.5353 33.7821 36.6432 33.7127C36.7512 33.6433 36.878 33.6092 37.0062 33.6152H39.5348L40.8358 30.8147C40.8924 30.7055 40.978 30.614 41.0832 30.5502C41.1884 30.4865 41.3091 30.4529 41.4321 30.4531C41.5551 30.4534 41.6756 30.4875 41.7805 30.5517C41.8854 30.6159 41.9706 30.7078 42.0268 30.8172V30.8172Z" stroke="black" stroke-width="1.26432" stroke-linecap="round" stroke-linejoin="round"/>'
)
competition_svg = (
        competition_svg
        + '<path d="M41.4238 46.2578V51.9473" stroke="black" stroke-width="1.26432" stroke-linecap="round" stroke-linejoin="round"/>'
)
competition_svg = (
        competition_svg
        + '<path d="M33.8359 56.3704C33.8359 53.9265 37.2319 51.9453 41.4219 51.9453C45.6118 51.9453 49.0078 53.9265 49.0078 56.3704H33.8359Z" stroke="black" stroke-width="1.26432" stroke-linecap="round" stroke-linejoin="round"/>'
)
competition_svg = (
        competition_svg
        + '<path d="M49.7676 38.7098C49.1999 44.3891 42.3865 48.6537 36.7982 44.7482C35.7247 43.9693 34.8314 42.9685 34.1789 41.8138C33.5264 40.6591 33.13 39.3776 33.0166 38.0561L32.0051 27.9884C31.9963 27.9002 32.006 27.8111 32.0338 27.727C32.0616 27.6428 32.1067 27.5655 32.1664 27.4999C32.226 27.4343 32.2987 27.382 32.3798 27.3464C32.461 27.3107 32.5487 27.2925 32.6373 27.293H50.2114C50.3 27.2925 50.3877 27.3107 50.4688 27.3464C50.5499 27.382 50.6227 27.4343 50.6823 27.4999C50.7419 27.5655 50.787 27.6428 50.8148 27.727C50.8426 27.8111 50.8524 27.9002 50.8435 27.9884L49.7676 38.7098Z" stroke="black" stroke-width="1.26432" stroke-linecap="round" stroke-linejoin="round"/>'
)
competition_svg = competition_svg + "</g>"
competition_svg = (
        competition_svg
        + '<circle cx="41.4217" cy="41.8299" r="39.4862" stroke="#5ac6cd" stroke-width="3"/>'
)
competition_svg = competition_svg + "<defs>"
competition_svg = competition_svg + '<clipPath id="clip0_226_206">'
competition_svg = (
        competition_svg
        + '<rect width="30.3437" height="30.3437" fill="white" transform="translate(26.25 26.6562)"/>'
)
competition_svg = competition_svg + "</clipPath>"
competition_svg = competition_svg + "</defs>"
competition_svg = competition_svg + "</svg>"

flexibility_svg = '<svg style="width:100%" viewBox="0 0 83 83" fill="none" xmlns="http://www.w3.org/2000/svg">'
flexibility_svg = flexibility_svg + '<g clip-path="url(#clip0_226_211)">'
flexibility_svg = (
        flexibility_svg
        + '<path d="M38.1211 31.6104C38.1211 32.4404 38.4508 33.2365 39.0378 33.8235C39.6248 34.4105 40.4209 34.7402 41.251 34.7402C42.0811 34.7402 42.8772 34.4105 43.4641 33.8235C44.0511 33.2365 44.3809 32.4404 44.3809 31.6104C44.3809 30.7803 44.0511 29.9842 43.4641 29.3972C42.8772 28.8102 42.0811 28.4805 41.251 28.4805C40.4209 28.4805 39.6248 28.8102 39.0378 29.3972C38.4508 29.9842 38.1211 30.7803 38.1211 31.6104Z" stroke="black" stroke-width="1.25195" stroke-linecap="round" stroke-linejoin="round"/>'
)
flexibility_svg = (
        flexibility_svg
        + '<path d="M51.8916 49.7617H46.5508L43.3921 45.7016C43.221 45.4819 43.128 45.2114 43.1279 44.9329V40.998H53.1436C53.6416 40.998 54.1193 40.8002 54.4714 40.448C54.8236 40.0958 55.0215 39.6182 55.0215 39.1201C55.0215 38.6221 54.8236 38.1444 54.4714 37.7922C54.1193 37.44 53.6416 37.2422 53.1436 37.2422H29.3564C28.8584 37.2422 28.3807 37.44 28.0285 37.7922C27.6764 38.1444 27.4785 38.6221 27.4785 39.1201C27.4785 39.6182 27.6764 40.0958 28.0285 40.448C28.3807 40.8002 28.8584 40.998 29.3564 40.998H39.3721V44.1279H36.8682C35.706 44.1279 34.5915 44.5896 33.7697 45.4113C32.948 46.2331 32.4863 47.3476 32.4863 48.5098V51.6396C32.4863 52.1377 32.6842 52.6154 33.0364 52.9675C33.3885 53.3197 33.8662 53.5176 34.3643 53.5176C34.8623 53.5176 35.34 53.3197 35.6922 52.9675C36.0443 52.6154 36.2422 52.1377 36.2422 51.6396V48.5098C36.2422 48.3437 36.3081 48.1845 36.4255 48.0671C36.5429 47.9497 36.7021 47.8838 36.8682 47.8838H40.3323L44.1508 52.7927C44.3262 53.0182 44.5508 53.2008 44.8075 53.3264C45.0641 53.452 45.3461 53.5174 45.6318 53.5176H51.8916C52.3897 53.5176 52.8673 53.3197 53.2195 52.9675C53.5717 52.6154 53.7695 52.1377 53.7695 51.6396C53.7695 51.1416 53.5717 50.6639 53.2195 50.3118C52.8673 49.9596 52.3897 49.7617 51.8916 49.7617Z" stroke="black" stroke-width="1.25195" stroke-linecap="round" stroke-linejoin="round"/>'
)
flexibility_svg = (
        flexibility_svg
        + '<path d="M39.373 44.1289H43.1289" stroke="black" stroke-width="1.25195" stroke-linecap="round" stroke-linejoin="round"/>'
)
flexibility_svg = flexibility_svg + "</g>"
flexibility_svg = (
        flexibility_svg
        + '<circle cx="41.2499" cy="41.0018" r="39.4862" stroke="#fec353" stroke-width="3"/>'
)
flexibility_svg = flexibility_svg + "<defs>"
flexibility_svg = flexibility_svg + '<clipPath id="clip0_226_211">'
flexibility_svg = (
        flexibility_svg
        + '<rect width="30.0469" height="30.0469" fill="white" transform="translate(26.2266 25.9766)"/>'
)
flexibility_svg = flexibility_svg + "</clipPath>"
flexibility_svg = flexibility_svg + "</defs>"
flexibility_svg = flexibility_svg + "</svg>"

creativity_svg = '<svg style="width:100%" viewBox="0 0 83 83" fill="none" xmlns="http://www.w3.org/2000/svg">'
creativity_svg = creativity_svg + '<g clip-path="url(#clip0_226_210)">'
creativity_svg = (
        creativity_svg
        + '<path d="M45.7275 33.4994L30.1035 49.1289L33.8559 52.88L49.48 37.2505L45.7275 33.4994Z" stroke="black" stroke-width="1.25019" stroke-linecap="round" stroke-linejoin="round"/>'
)
creativity_svg = (
        creativity_svg
        + '<path d="M43.9277 46.7625L53.2291 55.3788C55.7295 55.3788 56.3546 54.7537 56.3546 52.2534L46.4044 44.3672" stroke="black" stroke-width="1.25019" stroke-linecap="round" stroke-linejoin="round"/>'
)
creativity_svg = (
        creativity_svg
        + '<path d="M55.1064 31.625C55.5774 32.1359 55.8389 32.8054 55.8389 33.5003C55.8389 34.1952 55.5774 34.8646 55.1064 35.3756L48.8555 41.6265" stroke="black" stroke-width="1.25019" stroke-linecap="round" stroke-linejoin="round"/>'
)
creativity_svg = (
        creativity_svg
        + '<path d="M29.7894 53.1914L27.6016 55.3792" stroke="black" stroke-width="1.25019" stroke-linecap="round" stroke-linejoin="round"/>'
)
creativity_svg = (
        creativity_svg
        + '<path d="M52.6044 26.6241L45.7285 33.5L49.4794 37.2509L56.3553 30.375L52.6044 26.6241Z" stroke="black" stroke-width="1.25019" stroke-linecap="round" stroke-linejoin="round"/>'
)
creativity_svg = (
        creativity_svg
        + '<path d="M31.0381 50.0664L28.8516 52.253L30.7268 54.1295L32.9147 51.9417" stroke="black" stroke-width="1.25019" stroke-linecap="round" stroke-linejoin="round"/>'
)
creativity_svg = (
        creativity_svg
        + '<path d="M30.727 26.625C30.4982 31.3019 34.7488 30.7269 36.5779 32.0896C37.5105 32.7954 38.1277 33.8401 38.2959 34.9975C38.4642 36.155 38.1699 37.3321 37.4768 38.2742C32.7861 44.5552 23.7347 33.376 30.727 26.625Z" stroke="black" stroke-width="1.25019" stroke-linecap="round" stroke-linejoin="round"/>'
)
creativity_svg = creativity_svg + "</g>"
creativity_svg = (
        creativity_svg
        + '<circle cx="41.9784" cy="41.0018" r="39.4862" stroke="#fec353" stroke-width="3"/>'
)
creativity_svg = creativity_svg + "<defs>"
creativity_svg = creativity_svg + '<clipPath id="clip0_226_210">'
creativity_svg = (
        creativity_svg
        + '<rect width="30.0045" height="30.0045" fill="white" transform="translate(26.9766 26)"/>'
)
creativity_svg = creativity_svg + "</clipPath>"
creativity_svg = creativity_svg + "</defs>"
creativity_svg = creativity_svg + "</svg>"

equity_svg = '<svg style="width:100%" viewBox="0 0 83 83" fill="none" xmlns="http://www.w3.org/2000/svg">'
equity_svg = equity_svg + '<g clip-path="url(#clip0_226_204)">'
equity_svg = (
        equity_svg
        + '<path d="M41.6875 33.707V52.8435" stroke="black" stroke-width="1.27576" stroke-linecap="round" stroke-linejoin="round"/>'
)
equity_svg = (
        equity_svg
        + '<path d="M37.9629 52.8438H45.3764" stroke="black" stroke-width="1.27576" stroke-linecap="round" stroke-linejoin="round"/>'
)
equity_svg = (
        equity_svg
        + '<path d="M27.6562 41.3598L32.1202 31.1562L36.5687 41.3598" stroke="black" stroke-width="1.27576" stroke-linecap="round" stroke-linejoin="round"/>'
)
equity_svg = (
        equity_svg
        + '<path d="M39.8837 31.1562H30.207" stroke="black" stroke-width="1.27576" stroke-linecap="round" stroke-linejoin="round"/>'
)
equity_svg = (
        equity_svg
        + '<path d="M36.5846 41.3594C36.5846 42.5436 36.1142 43.6793 35.2768 44.5167C34.4394 45.3541 33.3037 45.8246 32.1195 45.8246C30.9352 45.8246 29.7995 45.3541 28.9621 44.5167C28.1247 43.6793 27.6543 42.5436 27.6543 41.3594H36.5846Z" stroke="black" stroke-width="1.27576" stroke-linecap="round" stroke-linejoin="round"/>'
)
equity_svg = (
        equity_svg
        + '<path d="M55.7191 41.3598L51.2552 31.1562L46.8066 41.3598" stroke="black" stroke-width="1.27576" stroke-linecap="round" stroke-linejoin="round"/>'
)
equity_svg = (
        equity_svg
        + '<path d="M43.4941 31.1562H53.1708" stroke="black" stroke-width="1.27576" stroke-linecap="round" stroke-linejoin="round"/>'
)
equity_svg = (
        equity_svg
        + '<path d="M46.7891 41.3594C46.7891 42.5436 47.2595 43.6793 48.0969 44.5167C48.9343 45.3541 50.07 45.8246 51.2542 45.8246C52.4385 45.8246 53.5742 45.3541 54.4116 44.5167C55.249 43.6793 55.7194 42.5436 55.7194 41.3594H46.7891Z" stroke="black" stroke-width="1.27576" stroke-linecap="round" stroke-linejoin="round"/>'
)
equity_svg = (
        equity_svg
        + '<path d="M39.7754 31.7926C39.7754 32.3001 39.977 32.7868 40.3359 33.1457C40.6948 33.5046 41.1815 33.7062 41.689 33.7062C42.1966 33.7062 42.6833 33.5046 43.0422 33.1457C43.4011 32.7868 43.6027 32.3001 43.6027 31.7926C43.6027 31.285 43.4011 30.7983 43.0422 30.4394C42.6833 30.0805 42.1966 29.8789 41.689 29.8789C41.1815 29.8789 40.6948 30.0805 40.3359 30.4394C39.977 30.7983 39.7754 31.285 39.7754 31.7926V31.7926Z" stroke="black" stroke-width="1.27576" stroke-linecap="round" stroke-linejoin="round"/>'
)
equity_svg = equity_svg + "</g>"
equity_svg = (
        equity_svg
        + '<circle cx="41.6874" cy="41.3612" r="39.4862" stroke="#C53E97" stroke-width="3"/>'
)
equity_svg = equity_svg + "<defs>"
equity_svg = equity_svg + '<clipPath id="clip0_226_204">'
equity_svg = (
        equity_svg
        + '<rect width="30.6184" height="30.6184" fill="white" transform="translate(26.3789 26.0547)"/>'
)
equity_svg = equity_svg + "</clipPath>"
equity_svg = equity_svg + "</defs>"
equity_svg = equity_svg + "</svg>"


def error_response(error_str):
    data = {"error": error_str}
    print(json.dumps(data))
    return {"statusCode": 500, "body": json.dumps({"data": data})}


"""
to find plotname in custome fields and return plot score
Args:
    param1: plot name
    param2: list of score and plot name
Returns:
    given plot score.
"""


def getPlotScore(plotName, custom_fields):
    score = 0
    givenPlots = custom_fields.get("purpose_plot_list")
    for plot in givenPlots:
        if plotName == plot.get("purpose_plot").get("plot"):
            score = plot.get("purpose_plot").get("score")
            score = float(score) * 20
            break
    return score


"""
calculate the score of all bar5 text
Args:
    param1: all bar5 text list
    param2: list of score and plot name
Returns:
    scores list.
"""


def get_scores(icons_label, custom_fields):
    scores = []
    for text in icons_label:
        plotScore = getPlotScore(text, custom_fields)
        scores.append(plotScore)
    return scores


# """
# calculate the score of all bar5 text
# Args:
#     param1: all bar5 text list
#     param2: list of score and plot name
# Returns:
#     scores list.
# """
def get_heights(scores):
    heights = []
    for i in scores:
        heights.append(i * 8)
    return heights


"""
to create all background grey bar circle and label bar
Args:
    param1: map object
    param2: list of angle to create grey bars in anti clockwise direction
    param3: list of color to fill label bars
    param4: width
"""


def grey_bar_creation(ax, angles, colors, width):
    bar4_max_height = 350
    bar5_max_height = 1500
    bar_width = 0.55
    bar_background_color = "#e7e6e6"
    bar1_bottom = 1000
    bar2_bottom = bar1_bottom + 200 + 150
    bar3_bottom = bar2_bottom + 280 + 150
    bar4_bottom = bar3_bottom + 320 + 200
    bar5_bottom = bar4_bottom + bar4_max_height

    # first grey bar
    ax.bar(
        x=angles,
        height=200,
        width=bar_width,
        bottom=bar1_bottom,
        linewidth=10,
        color=bar_background_color,
        edgecolor="none",
    )
    # second grey bar
    ax.bar(
        x=angles,
        height=280,
        width=bar_width,
        bottom=bar2_bottom,
        linewidth=10,
        color=bar_background_color,
        edgecolor="none",
    )
    # third grey bar
    ax.bar(
        x=angles,
        height=320,
        width=bar_width,
        bottom=bar3_bottom,
        linewidth=20,
        color=bar_background_color,
        edgecolor="none",
    )
    # fourth circle
    ax.bar(
        x=angles,
        height=bar4_max_height,
        width=width,
        bottom=bar4_bottom,
        linewidth=0,
        color=colors,
        edgecolor="white",
    )
    # Outer grey circle
    ax.bar(
        x=angles,
        height=bar5_max_height,
        width=width,
        bottom=bar5_bottom,
        linewidth=0,
        color="#f2f1f1",
        edgecolor="white",
    )


"""
to create score bar that reperesent score progress depends on score data
Args:
    param1: map object
    param2: list of angle to create score bars anti clockwise direction
    param3: list of color to fill score bars
    param4: first score progress bar height near center in y direction
    param5: second score progress bar height near center in y direction
    param6: third score progress bar height near center in y direction
"""


def score_bar_creation(ax, angles, colors, heights_bar1, heights_bar2, heights_bar3):
    bar_width = 0.55
    bar1_bottom = 1000
    bar2_bottom = bar1_bottom + 200 + 150
    bar3_bottom = bar2_bottom + 280 + 150

    # first data bar
    ax.bar(
        x=angles,
        height=heights_bar1,
        width=bar_width,
        bottom=bar1_bottom,
        linewidth=5,
        color=colors,
        edgecolor="none",
    )
    # second data bar
    ax.bar(
        x=angles,
        height=heights_bar2,
        width=bar_width,
        bottom=bar2_bottom,
        linewidth=7,
        color=colors,
        edgecolor="none",
    )
    # third data bar
    ax.bar(
        x=angles,
        height=heights_bar3,
        width=bar_width,
        bottom=bar3_bottom,
        linewidth=20,
        color=colors,
        edgecolor="none",
    )


"""
to create height of score bar depends on score data
Args:
    param1: heights
Returns:
    dict that contains first, second and third score bar height
"""


def score_bar_heights_creation(heights):
    start_time_setting_bar_heights = time.perf_counter()
    heights_bar1 = []
    heights_bar2 = []
    heights_bar3 = []

    bar_min_height = 160
    bar1_max_height = 292
    bar2_max_height = 54
    bar_min_bar1_max_total = bar_min_height + bar1_max_height
    bar_min_bar1_bar2_max_height_total = bar_min_bar1_max_total + bar2_max_height

    for i in heights:
        if i > bar_min_height:
            heights_bar1.append(200)
        else:
            heights_bar1.append(0)

    for i in heights:
        if i > bar_min_bar1_max_total:
            heights_bar2.append(280)
        else:
            heights_bar2.append(0)

    for i in heights:
        if i > bar_min_bar1_bar2_max_height_total:
            heights_bar3.append(320)
        else:
            heights_bar3.append(0)

    score_bar_heights = {
        "heights_bar1": heights_bar1,
        "heights_bar2": heights_bar2,
        "heights_bar3": heights_bar3,
    }
    end_time_setting_bar_heights = time.perf_counter()
    print(
        f"Time taken setting Spiral Bar Heights: {end_time_setting_bar_heights - start_time_setting_bar_heights:0.4f} seconds"
    )

    return score_bar_heights


"""
to create lebels of different data score
Args:
    param1: map object
    param1: list of angle to create score bars anti clockwise direction
Returns:
    dict that contains first, second and third score bar height
"""


def labels_creation(ax, angles, labels_text):
    rotations = [306, 342, 378, 414, 450, 306, 325, 398, 414, 360.0]

    start_time_positioning_text = time.perf_counter()
    bar4_min_text_position = 2300
    text_position_bars4 = [
        {"x": 0, "y": bar4_min_text_position + 150},
        {"x": 0, "y": bar4_min_text_position},
        {"x": 0, "y": bar4_min_text_position},
        {"x": 0, "y": bar4_min_text_position + 150},
        {"x": 0, "y": bar4_min_text_position},
        {"x": 0, "y": bar4_min_text_position},
        {"x": -0.3, "y": bar4_min_text_position + 200},
        {"x": 0.32, "y": bar4_min_text_position + 175},
        {"x": 0, "y": bar4_min_text_position},
        {"x": 0, "y": bar4_min_text_position},
    ]

    i = 0
    for angle in angles:
        # bar4 labels are rotated. Rotation must be specified in degrees
        ax.text(
            x=angle + text_position_bars4[i].get("x"),
            y=text_position_bars4[i].get("y"),
            s=labels_text[i],
            fontsize=8,
            ha="center",
            va="center",
            weight="bold",
            rotation=rotations[i],
            rotation_mode="anchor",
        )
        i = i + 1

    end_time_positioning_text = time.perf_counter()
    print(
        f"Time taken for positioning text: {end_time_positioning_text - start_time_positioning_text:0.4f} seconds"
    )


"""
to create lebels of images in fifth circle bar
Args:
    param1: map object
    param2: list of angle to create score bars anti clockwise direction
    param3: list of text that represents perticular image
"""


def icons_label_creation(ax, angles, icons_label):
    start_time_positioning_text = time.perf_counter()
    bar5_min_text_position = 2750
    text_position = [
        {"x": -0.15, "y": bar5_min_text_position + 400},
        {"x": -0.08, "y": bar5_min_text_position + 150},
        {"x": 0.02, "y": bar5_min_text_position + 150},
        {"x": 0.14, "y": bar5_min_text_position + 350},
        {"x": 0.12, "y": bar5_min_text_position + 650},
        {"x": 0.10, "y": bar5_min_text_position + 950},
        {"x": 0.05, "y": bar5_min_text_position + 1200},
        {"x": -0.04, "y": bar5_min_text_position + 1200},
        {"x": -0.10, "y": bar5_min_text_position + 1000},
        {"x": -0.12, "y": bar5_min_text_position + 650},
    ]
    i = 0
    for angle in angles:
        # Labels are rotated. Rotation must be specified in degrees
        ax.text(
            x=angle + text_position[i].get("x"),
            y=text_position[i].get("y"),
            s=icons_label[i],
            ha="center",
            va="center",
            fontsize=9,
            rotation_mode="anchor",
        )
        i = i + 1

    end_time_positioning_text = time.perf_counter()
    print(
        f"Time taken for positioning text: {end_time_positioning_text - start_time_positioning_text:0.4f} seconds"
    )


"""
to create image box in fifth circle
Args:
    param1: map object
    param2: list of angle to create score bars anti clockwise direction
"""


def icons_box_creation(ax, angles):
    start_time_positioning_img = time.perf_counter()
    i = 0
    bar5_image_position = 3400
    image_position = [
        {"x": -0.02, "y": bar5_image_position, "box_alignment": (1, 0.5)},
        {"x": -0.02, "y": bar5_image_position, "box_alignment": (0.5, 0.9)},
        {"x": -0.02, "y": bar5_image_position, "box_alignment": (0.5, 0.9)},
        {"x": 0, "y": bar5_image_position, "box_alignment": (0.1, 0.5)},
        {"x": -0.02, "y": bar5_image_position, "box_alignment": (0, 0.2)},
        {"x": -0.02, "y": bar5_image_position, "box_alignment": (0.4, 0)},
        {"x": 0, "y": bar5_image_position, "box_alignment": (0.5, -0.2)},
        {"x": 0, "y": bar5_image_position, "box_alignment": (0.5, -0.2)},
        {"x": 0.02, "y": bar5_image_position, "box_alignment": (0.7, -0.2)},
        {"x": 0.02, "y": bar5_image_position, "box_alignment": (1, 0.2)},
    ]

    bars5_icon_box = [
        skunk.Box(50, 50, "Service"),
        skunk.Box(50, 50, "Cohesion"),
        skunk.Box(50, 50, "Quality"),
        skunk.Box(50, 50, "Certainty"),
        skunk.Box(50, 50, "Legacy"),
        skunk.Box(50, 50, "Authority"),
        skunk.Box(50, 50, "Competition"),
        skunk.Box(50, 50, "Flexibility"),
        skunk.Box(50, 50, "Creativity"),
        skunk.Box(50, 50, "Equity"),
    ]
    for angle in angles:
        # Labels are rotated. Rotation must be specified in degrees
        ax.add_artist(
            AnnotationBbox(
                bars5_icon_box[i],
                (angle + image_position[i].get("x"), image_position[i].get("y")),
                frameon=False,
            )
        )
        i = i + 1

    end_time_positioning_img = time.perf_counter()
    print(
        f"Time taken for positioning img: {end_time_positioning_img - start_time_positioning_img:0.4f} seconds"
    )


"""
to link svg image with images box in fifth circle
Returns:
    svg of chart
"""


def icons_creation():
    start_time_base64_str = time.perf_counter()
    svg = skunk.insert(
        {
            "Service": service_svg,
            "Cohesion": cohesion_svg,
            "Quality": quality_svg,
            "Certainty": certainty_svg,
            "Legacy": legacy_svg,
            "Authority": authority_svg,
            "Competition": competition_svg,
            "Flexibility": flexibility_svg,
            "Creativity": creativity_svg,
            "Equity": equity_svg,
        }
    )
    end_time_base64_str = time.perf_counter()
    print(
        f"Time taken for inserting svg and str: {end_time_base64_str - start_time_base64_str:0.4f} seconds"
    )
    return svg


"""
to create a circular chart that represent score progress
Args:
    param1: request data that contains labels and score
Returns:
    string of chart
"""


# to chceck score elements with 4 and 6  -- negative
# check score if score goes less than 0 and gretter than 5  -- negative
# purpose_plot_list list must be gretter than 5


def make_chart(request_data):
    # Build a dataset
    start_time_make_chart = time.perf_counter()
    df = pd.DataFrame(
        {
            "Name": ["item " + str(i) for i in list(range(1, 11))],
            "Value": random.sample(range(10, 800), 10),
        }
    )
    # set figure size
    plt.figure(figsize=(10, 10))
    # plot polar axis
    ax = plt.subplot(111, polar=True)
    plt.tight_layout(pad=1.5)
    pie = 3.141592653589793
    # remove grid
    plt.axis("off")
    # Compute the width of each bar. In total we have 2*Pi = 360°
    width = 2 * pie / len(df.index)
    # Compute the angle each bar is centered on:
    indexes = list(range(1, len(df.index) + 1))
    angles = [element * width for element in indexes]
    # getting labels and score
    custom_fields = request_data.get("custom_fields")
    # to set colors that represent different score
    colors = [
        "#df9cc5",
        "#df9cc5",
        "#f9b4a9",
        "#f9b4a9",
        "#f9b4a9",
        "#6fcbd1",
        "#6fcbd1",
        "#ffe1a7",
        "#ffe1a7",
        "#df9cc5",
    ]
    # to set labels of images
    icons_label = [
        "Service",
        "Cohesion",
        "Quality",
        "Certainty",
        "Legacy",
        "Authority",
        "Competition",
        "Flexibility",
        "Creativity",
        "Equity",
    ]
    # to get scores
    scores = get_scores(icons_label, custom_fields)
    # to get heights
    heights = get_heights(scores)
    # to create score bar heights
    score_bar_heights = score_bar_heights_creation(heights)
    print("score_bar_heights")
    print(score_bar_heights)
    heights_bar1 = score_bar_heights.get("heights_bar1")
    heights_bar2 = score_bar_heights.get("heights_bar2")
    heights_bar3 = score_bar_heights.get("heights_bar3")
    # calling the function that creates background grey bar and label bar
    grey_bar_creation(ax, angles, colors, width)
    # calling the function that creates score bar
    score_bar_creation(ax, angles, colors, heights_bar1, heights_bar2, heights_bar3)
    # set labels text
    labels_text = ["PROTECT", "", "", "PRESERVE", "", "", "PERFORM", "PIVOT", "", ""]
    # calling the function that creates labels
    labels_creation(ax, angles, labels_text)
    # calling the function that creates images text in fifth bar
    icons_label_creation(ax, angles, icons_label)
    # calling the function that creates images svg image box fifth bar
    icons_box_creation(ax, angles)
    # calling the function that put images in images box and return svg chart
    svg = icons_creation()
    # to convert chart in base64 encoded string
    chart_svg = base64.b64encode(bytes(svg, "utf-8"))
    # end time of chart creation
    end_time_make_chart = time.perf_counter()
    print(
        f"Time taken for Chart: {end_time_make_chart - start_time_make_chart:0.4f} seconds"
    )

    return chart_svg


def radar_factory(num_vars, frame="circle"):
    start_time_make_chart = time.perf_counter()
    # calculate evenly-spaced axis angles
    theta = np.linspace(0, 2 * np.pi, num_vars, endpoint=False)

    class RadarTransform(PolarAxes.PolarTransform):
        def transform_path_non_affine(self, path):
            # Paths with non-unit interpolation steps correspond to gridlines,
            # in which case we force interpolation (to defeat PolarTransform's
            # auto conversion to circular arcs).
            if path._interpolation_steps > 1:
                path = path.interpolated(num_vars)
            return Path(self.transform(path.vertices), path.codes)

    class RadarAxes(PolarAxes):
        name = "radar"
        PolarTransform = RadarTransform

        # use 1 line segment to connect specified points
        RESOLUTION = 1

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # rotate plot such that the first axis is at the top
            self.set_theta_direction("clockwise")
            self.set_theta_zero_location("N")

        def fill(self, *args, closed=True, **kwargs):
            """Override fill so that line is closed by default"""
            return super().fill(closed=closed, *args, **kwargs)

        def plot(self, *args, **kwargs):
            """Override plot so that line is closed by default"""
            lines = super().plot(*args, **kwargs)
            for line in lines:
                self._close_line(line)

        def _close_line(self, line):
            x, y = line.get_data()
            # FIXME: markers at x[0], y[0] get doubled-up
            if x[0] != x[-1]:
                x = np.append(x, x[0])
                y = np.append(y, y[0])
                line.set_data(x, y)

        def set_varlabels(self, labels):
            # theta = [0, 1.25663706, 2.51327412, 3.76991118, 5.02654825]
            self.set_thetagrids(np.degrees(theta), labels)

        def _gen_axes_patch(self):
            # The Axes patch must be centered at (0.5, 0.5) and of radius 0.5
            # in axes coordinates.
            if frame == "circle":
                return Circle((0.5, 0.5), 0.5)
            elif frame == "polygon":
                return RegularPolygon((0.5, 0.5), num_vars, radius=0.5, edgecolor="k")
            else:
                raise ValueError("Unknown value for 'frame': %s" % frame)

        def _gen_axes_spines(self):
            if frame == "circle":
                return super()._gen_axes_spines()
            elif frame == "polygon":
                # spine_type must be 'left'/'right'/'top'/'bottom'/'circle'.
                spine = Spine(
                    axes=self,
                    spine_type="circle",
                    path=Path.unit_regular_polygon(num_vars),
                )
                # unit_regular_polygon gives a polygon of radius 1 centered at
                # (0, 0) but we want a polygon of radius 0.5 centered at (0.5,
                # 0.5) in axes coordinates.
                spine.set_transform(
                    Affine2D().scale(0).translate(0.1, 0.1) + self.transAxes
                )
                return {"polar": spine}
            else:
                raise ValueError("Unknown value for 'frame': %s" % frame)

    register_projection(RadarAxes)
    end_time_make_chart = time.perf_counter()
    print(
        f"Time taken for Theta: {end_time_make_chart - start_time_make_chart:0.4f} seconds"
    )

    return theta


def radar_pt_desc(label):
    description = ""
    if label == "Human Capital":
        description = "Knowledge and capability to apply human capital practices to acquire, mobilize, motivate and develop highly effective teams and individuals."
        # set Operations & Execution description
    elif label == "Operations & Execution":
        description = "Knowledge and skills in defining and driving business practices, implementing methods and processes, and allocating resources to ensure efficient and effective execution of strategy."
        # set Strategy & Innovation description
    elif label == "Strategy & Innovation":
        description = "Demonstrated capability to think holistically and act decisively to shape the strategic vision and drive innovation."
        # set Commercial description
    elif label == "Commercial":
        description = "Strong understanding of how the business functions and competes and ability to shape key commercial factors to drive customer value and business growth."
        # Finance description
    elif label == "Finance":
        description = "Knowledge and skills in applying financial management principles and techniques to ensure fiscally sound decisions and investments."

    return description


def scatter_dots(ax, theta, case_data):
    """Radar Chart Scatter dots"""
    scatter = ax.scatter(
        theta,
        case_data,
        s=200,
        marker="o",
        color="#f66536",
        zorder=4,
        alpha=1,
        clip_on=False,
    )
    return scatter


def scatter_tooltips(ax, theta, case_data, pos_num):
    """Radar Chart Scatter tooltips - position & styling functions"""
    tooltip = ax.text(
        x=theta,
        y=case_data + pos_num,
        s=case_data,
        ha="center",
        va="center",
        wrap=True,
        zorder=4,
        fontsize=30,
        alpha=1,
        rotation_mode="anchor",
        color="#ffffff",
        bbox=dict(boxstyle="round,pad=0.35", fc="#4f5666", ec="none"),
    )
    return tooltip


def label_texts(ax, x_val, y_val, label_txt, ha_pos):
    """Radar Chart Positioning of outer labels"""
    label_text = ax.text(
        x=x_val,
        y=y_val,
        s=label_txt,
        wrap=True,
        ha=ha_pos,
        va="center",
        fontsize=24,
        alpha=0.5,
        color="black",
        rotation_mode="anchor",
        bbox=dict(boxstyle="square,pad=0", fc="w", ec="none"),
    )
    return label_text


def label_texts_tooltips(ax, x_val, y_val, label_txt):
    """Radar Chart Label tooltips - position & styling function"""
    label_tooltip = ax.text(
        x=x_val,
        y=y_val,
        s=radar_pt_desc(label_txt),
        ha="center",
        va="center",
        wrap=True,
        zorder=5,
        fontsize=24,
        alpha=1,
        rotation_mode="anchor",
        color="#ffffff",
        bbox=dict(boxstyle="round,pad=0.35", fc="#4f5666", ec="none"),
    )
    return label_tooltip


def make_radar_graph(event, context):
    request_data = event.get("request_data", {})
    custom_fields = request_data.get("custom_fields")
    lead_expertise_list = custom_fields.get("lead_expertise_list")

    pic_hash = ""
    case_data = []
    labels = []

    if not lead_expertise_list:
        case_data = [0, 0, 0, 0, 0]
        labels = [
            "Human Capital",
            "Operations & Execution",
            "Strategy & Innovation",
            "Commercial",
            "Finance",
        ]
    else:
        for item in lead_expertise_list:
            score = item.get("lead_expertise").get("score", 0) or 0
            score = round(score, 2)
            label = item.get("lead_expertise").get("expertise")
            case_data.append(score)
            labels.append(label)

    N = 5
    theta = radar_factory(N, frame="polygon")

    fig, ax = plt.subplots(
        figsize=(11.8, 8), nrows=1, ncols=1, subplot_kw=dict(projection="radar")
    )

    ax.set_rgrids([0, 1, 2, 3, 4, 5])
    if not lead_expertise_list:
        ax.scatter(
            theta,
            [5, 5, 5, 5, 5],
            s=360,
            marker="s",
            color="#ffffff",
            edgecolor="#aeb9c7",
            zorder=2,
            alpha=1,
            clip_on=False,
        )
    else:
        ax.scatter(
            theta,
            [5, 5, 5, 5, 5],
            s=200,
            marker="s",
            color="#ffffff",
            edgecolor="#aeb9c7",
            zorder=2,
            alpha=1,
            clip_on=False,
        )

    # Radar map pointer's loop - dots & tooltip placements
    for i in range(len(labels)):
        count = i + 1
        scatter_dots(ax, theta[i], case_data[i]).set_gid("scatter" + str(count))
        if lead_expertise_list:
            scatter_tooltips(ax, theta[i], case_data[i], 1.2).set_gid(
                "scatter" + str(count) + "_tooltip"
            )

    ax.plot(theta, case_data, color="#f66536", zorder=2, lw=4)
    ax.fill(theta, case_data, facecolor="#f66536", alpha=0.25, zorder=3)

    ax.set_xticks(theta)
    ax.set_yticks([0, 1, 2, 3, 4, 5])
    ax.set_yticklabels([])
    ax.set_varlabels([])

    # radar map outer label 1 - top
    label_texts(ax, 0, 5.5, labels[0], "center").set_gid("text1")
    label_texts_tooltips(ax, 0, 4.27, labels[0]).set_gid("text1_tooltip")
    # radar map outer label 2 - top right
    label_texts(ax, 1.3, 5.33, labels[1], "left").set_gid("text2")
    label_texts_tooltips(ax, 0.68, 4.6, labels[1]).set_gid("text2_tooltip")
    # radar map outer label 3 - bottom right
    label_texts(ax, 2.42327412, 6.2, labels[2], "center").set_gid("text3")
    label_texts_tooltips(ax, 2.38, 4.7, labels[2]).set_gid("text3_tooltip")
    # radar map outer label 4 bottom left
    label_texts(ax, 3.79991118, 5.9, labels[3], "center").set_gid("text4")
    label_texts_tooltips(ax, 3.99, 4.75, labels[3]).set_gid("text4_tooltip")
    # radar map outer label 5 top left
    label_texts(ax, 5.010, 5.33, labels[4], "right").set_gid("text5")
    label_texts_tooltips(ax, 5.5, 4.35, labels[4]).set_gid("text5_tooltip")

    plt.subplots_adjust(bottom=0, hspace=0, wspace=0)
    start_time_make_chart = time.perf_counter()
    f = io.BytesIO()
    # plt.savefig(pic_IObytes, bbox_inches='tight', pad_inches=0, format='png')
    plt.savefig(f, format="svg")
    pic_hash = f.getvalue().decode("utf-8")

    # plt.show()
    end_time_make_chart = time.perf_counter()
    print(
        f"Time taken for Radar Chart Base64: {end_time_make_chart - start_time_make_chart:0.4f} seconds"
    )

    return pic_hash


def get_esg_val(custom_fields):
    purpose_priority_list = custom_fields.get("purpose_priority_list", "")
    esg_data_html = ""
    for item in purpose_priority_list:
        if "purpose_priority" in item:
            purpose_priority = item.get("purpose_priority")
            if purpose_priority and purpose_priority is not None:
                priority = purpose_priority.get("priority", "")
                if priority == "ESG Values":
                    description = purpose_priority.get("description")
                    esg_data_html = '<div style="padding:0">'
                    esg_data_html = esg_data_html + "<div><b>" + priority + "</b></div>"
                    esg_data_html = (
                            esg_data_html
                            + '<p style="padding:4px 10px 0 0">'
                            + description
                            + "</p>"
                    )
                    esg_data_html = esg_data_html + "</div>"

    return esg_data_html


def legend_group_info_data():
    protect_desc = (
        "Prioritizing the well-being of others while emphasizing sustainability, "
        "equity, and social justice. These values also describe how strongly an "
        "individual is likely to promote ESG concerns."
    )
    pivot_desc = (
        "Prioritizing change, novelty, new experiences, embracing challenges, "
        "and taking risks."
    )
    perform_desc = "Prioritizing profit, status, control, and succeeding over others."
    preserve_desc = (
        "Prioritizing tradition, consistency, and precision while avoiding risks "
        "or disruption."
    )

    legend_group_html = '<div style="padding:0">'
    legend_group_html = legend_group_html + "<div><b>Protect</b></div>"
    legend_group_html = (
            legend_group_html + '<p style="padding:0 10px 10px 0">' + protect_desc + "</p>"
    )
    legend_group_html = legend_group_html + "<div><b>Pivot</b></div>"
    legend_group_html = (
            legend_group_html + '<p style="padding:0 10px 10px 0">' + pivot_desc + "</p>"
    )
    legend_group_html = legend_group_html + "<div><b>Perform</b></div>"
    legend_group_html = (
            legend_group_html + '<p style="padding:0 10px 10px 0">' + perform_desc + "</p>"
    )
    legend_group_html = legend_group_html + "<div><b>Preserve</b></div>"
    legend_group_html = (
            legend_group_html + '<p style="padding:0 10px 10px 0">' + preserve_desc + "</p>"
    )

    return legend_group_html


def ch_profile_view_main_content_on_expand_handler(event, context):
    request_data = event.get("request_data", {})

    start_time = time.perf_counter()
    custom_fields = request_data.get("custom_fields")
    purpose_plot_list = custom_fields.get("purpose_plot_list")
    purpose_list = custom_fields.get("purpose_list")

    count_plot_list = len(purpose_plot_list)
    if count_plot_list < 5:
        return error_response("Data Not Found")

    start_time_html_chart_str = time.perf_counter()
    # chart = make_chart(request_data)
    # chart_str = chart.decode('utf-8')
    esg_html = get_esg_val(custom_fields)
    legend_group_html = legend_group_info_data()

    # plt.show()
    html = "<div>"
    html = html + '<div class="col-md-12" style="padding: 0 25px 0 0">'
    html = (
            html
            + '<div style="padding: 0 0 10px 0">Based on the leader’s responses, the values '
              "listed below are ranked from most to least prioritized. It is important to "
              "emphasize the these are shown in relative importance to one another, and no "
              "order of values is more desirable than others.</div>"
    )
    # html = html + '<img style="max-width:100%" src="data:image/svg+xml;base64,' + chart_str + '" alt="Purpose Plot" />'
    html = html + "</div>"

    html = html + '<div class="col-md-12" style="padding:10px 0 0;">'
    html = html + '<div style="padding: 10px 0;">'
    html = (
            html
            + '<ul style="list-style-type: none;padding:0;-moz-column-count: 2;-moz-column-gap: '
              '20px;-webkit-column-count: 2;-webkit-column-gap: 15px;column-count: 2;column-gap: 15px;"> '
    )

    # number = 0
    category = ""
    color = ""

    end_time_html_chart_str = time.perf_counter()
    print(
        f"Time taken for Chart HTML str: {end_time_html_chart_str - start_time_html_chart_str:0.4f} seconds"
    )

    # sort purpose list based on purpose rank
    def customSort(k):
        return int(k["purpose_details"]["purpose_rank"])

    purpose_list.sort(key=customSort)

    start_time_legends_loop = time.perf_counter()
    for obj in purpose_list:
        purpose_ranking = obj.get("purpose_details")

        if purpose_ranking.get("purpose_ranking_value") is None:
            continue
        text = purpose_ranking.get("purpose_ranking_value")
        rank = purpose_ranking.get("purpose_rank")
        svg_str = ""
        description = "Data Not Found"
        if purpose_ranking.get("purpose_ranking_description") is not None:
            description = purpose_ranking.get("purpose_ranking_description")

        if text == "Equity":
            svg_str = equity_svg
            category = "PROTECT"
            color = "#df9cc5"
        if text == "Service":
            svg_str = service_svg
            category = "PROTECT"
            color = "#df9cc5"
        if text == "Cohesion":
            svg_str = cohesion_svg
            category = "PROTECT"
            color = "#df9cc5"
        if text == "Quality":
            svg_str = quality_svg
            category = "PRESERVE"
            color = "#f9b4a9"
        if text == "Certainty":
            svg_str = certainty_svg
            category = "PRESERVE"
            color = "#f9b4a9"
        if text == "Legacy":
            svg_str = legacy_svg
            category = "PRESERVE"
            color = "#f9b4a9"

        if text == "Authority":
            svg_str = authority_svg
            category = "PERFORM"
            color = "#6fcbd1"

        if text == "Competition":
            svg_str = competition_svg
            category = "PERFORM"
            color = "#6fcbd1"
        if text == "Flexibility":
            svg_str = flexibility_svg
            category = "PIVOT"
            color = "#ffe1a7"
        if text == "Creativity":
            svg_str = creativity_svg
            category = "PIVOT"
            color = "#ffe1a7"

        # number = number + 1
        # number_str = str(number)
        html = (
                html
                + '<li style="padding:10px;border-radius:4px;background: #f1f1f1;margin: 0 0 '
                  '15px;min-height:105px;"> '
        )
        html = html + '<div style="display: flex;align-items: flex-start;">'
        html = html + '<div style="display:flex;">'
        html = (
                html
                + '<span style="font-size: 18px;color:#606060;align-self: center;">'
                + str(rank)
                + "</span>"
        )
        html = html + '<div style="margin:0 10px;width:40px;">' + svg_str + "</div>"
        html = html + "</div>"
        html = html + "<div>"
        html = html + '<div style="padding:0 0 5px 0">'
        html = html + '<span style="font-size: 15px;"><b>' + str(text) + "</b></span>"
        html = (
                html
                + '<span style="background:'
                + color
                + ";padding:2px 4px;display:inline-block;margin: 0 "
                  '3px;border-radius:4px;font-size: 13px;">' + category + "</span> "
        )
        html = html + "</div>"
        html = (
                html
                + '<p style="color:#6f6f6f;font-size: 14px!important;">'
                + description
                + "</p>"
        )
        html = html + "</div>"
        html = html + "</div>"
        html = html + "</li>"

    html = html + "</ul"
    html = html + "</div>"
    html = html + "</div>"
    html = html + legend_group_html
    html = html + esg_html
    html = html + "</div>"

    end_time_legends_loop = time.perf_counter()
    print(
        f"Time taken for Legends: {end_time_legends_loop - start_time_legends_loop:0.4f} seconds"
    )

    # plt.show()

    end_time = time.perf_counter()
    print(f"Time taken for Content on Expand: {end_time - start_time:0.4f} seconds")

    return {
        "statusCode": 200,
        # 'body': json.dumps({'data': data})
        "body": json.dumps({"html": html, "data": {}, "cache_ttl_seconds": 0}),
    }


# start function
def ch_profile_view_main_content_handler(event, context):
    # if desc is none put not data found
    # if element less than 5 put status code 500 and error message not data found
    # put perpose details from payload
    start_time = time.perf_counter()
    request_data = event.get("request_data", {})
    custom_fields = request_data.get("custom_fields")
    purpose_priority_list = custom_fields.get("purpose_priority_list", "")
    app_settings = event.get("app_settings", {})
    statement = app_settings.get("statement") or (
        "Motivations and values that drive a leader's impact on their team and the organization's culture."
    )

    html = '<div class="col-md-12" style="padding:0">'
    # html = html + '<div><b>Purpose</b></div>'
    html = html + '<div style="padding: 4px 0 15px 0">' + statement + "</div> "
    html = html + "</div>"

    # priorities description
    priorities = ["Primary Value", "Lowest Value"]
    description = "Data Not Found"
    html = html + '<div class="col-md-12" style="padding:0">'
    for priority in priorities:
        for item in purpose_priority_list:
            if item.get("purpose_priority") is not None:
                purpose_priority = item.get("purpose_priority", "")
                if (
                        purpose_priority.get("priority") == priority
                        and purpose_priority.get("description") is not None
                ):
                    description = purpose_priority.get("description")
                    break

        html = html + '<div class="col-md-6" style="padding:0">'
        html = html + "<div><b>" + priority + "</b></div>"
        html = html + '<p style="padding:4px 10px 0 0">' + description + "</p>"
        html = html + "</div>"
        description = "Data Not Found"
    html = html + "</div>"

    # print(html)
    end_time = time.perf_counter()
    print(
        f"Time taken for Profile View Main Content: {end_time - start_time:0.4f} seconds"
    )

    return {
        "statusCode": 200,
        "body": json.dumps({"html": html, "data": {}, "cache_ttl_seconds": 0}),
    }


def career_hub_profile_view_handler(event, context):
    start_time_make_chart = time.perf_counter()
    request_data = event.get("request_data", {})
    custom_fields = request_data.get("custom_fields", {})
    lead_expertise_list = custom_fields.get("lead_expertise_list", [])

    radar_graph_str = make_radar_graph(event, context)
    # radar_graph_str = radar_graph_str.decode('utf-8')

    html = '<div style="padding:0">'
    html = html + "<div><b>Impact Categories</b></div>"
    if lead_expertise_list:
        html = html + '<div style="padding: 4px 0 15px 0">Impact categories show the leader’s overall impact across five general types of business outcomes.</div>'
    else:
        html = html + "<div>No data available</div>"
    html = html + "</div>"
    html = html + '<div class="radar_graph_str"> ' + radar_graph_str + "</div> "
    style = """
    <style>
        .radar_graph_str svg { max-width: 100%; height:auto }
        #text1_tooltip, #text2_tooltip, #text3_tooltip, #text4_tooltip, #text5_tooltip,
        #scatter1_tooltip, #scatter2_tooltip, #scatter3_tooltip, #scatter4_tooltip,
        #scatter5_tooltip { display:none }
        #text1:hover ~ #text1_tooltip, #text2:hover ~ #text2_tooltip, #text3:hover ~ #text3_tooltip,
        #text4:hover ~ #text4_tooltip, #text5:hover ~ #text5_tooltip,
        #scatter1:hover ~ #scatter1_tooltip, #scatter2:hover ~ #scatter2_tooltip,
        #scatter3:hover ~ #scatter3_tooltip, #scatter4:hover ~ #scatter4_tooltip,
        #scatter5:hover ~ #scatter5_tooltip { display:block }
    </style>
    """
    html = html + style

    # print(html)
    end_time_make_chart = time.perf_counter()
    print(
        f"Time taken for Radar Chart: {end_time_make_chart - start_time_make_chart:0.4f} seconds"
    )

    return {
        "statusCode": 200,
        "body": json.dumps({"html": html, "data": {}, "cache_ttl_seconds": 0}),
    }


def app_handler(event, context):
    # request_data = event.get("request_data", {})
    trigger_name = event.get("trigger_name")
    # print('Trigger Name: ', trigger_name)
    # print('event: ', event)

    try:
        if trigger_name == "ch_profile_view_main_content":
            return ch_profile_view_main_content_handler(event, context)
        if trigger_name == "ch_profile_view_main_content_on_expand":
            return ch_profile_view_main_content_on_expand_handler(event, context)
        if trigger_name == "career_hub_profile_view":
            return career_hub_profile_view_handler(event, context)
        else:
            return error_response("Unknown trigger.")

    except Exception as e:
        data = {}
        error_str = "Something went wrong, traceback: {}".format(traceback.format_exc())
        print(error_str)
        data = {"error": repr(e), "stacktrace": traceback.format_exc()}
        return {"statusCode": 500, "body": json.dumps({"data": data})}
