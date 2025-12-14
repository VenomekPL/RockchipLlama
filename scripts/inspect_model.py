from rknnlite.api import RKNNLite
import os

rknn = RKNNLite()
model_path = "models/stable-diffusion-lcm/unet_lcm_512.rknn"
if not os.path.exists(model_path):
    print("Model not found")
    exit()

rknn.load_rknn(model_path)
rknn.init_runtime(core_mask=RKNNLite.NPU_CORE_0_1_2)

io_num = rknn.rknn_runtime.get_in_out_num()
print(f"IO Num: {io_num}")
n_input = io_num[0]

for i in range(n_input):
    attr = rknn.rknn_runtime.get_tensor_attr(i)
    print(f"Input {i}:")
    print(f"  name: {attr.name}")
    print(f"  dims: {attr.dims}")
    print(f"  n_dims: {attr.n_dims}")
    print(f"  type: {attr.type}")
    print(f"  fmt: {attr.fmt}")
    print(f"  size: {attr.size}")

rknn.release()
