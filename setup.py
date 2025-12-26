from setuptools import setup, Extension

setup(
    ext_modules=[
        Extension(
            name="abloom._abloom",
            sources=[
                "abloom/_abloom.c",
            ],
            extra_compile_args=["-O3"],
        )
    ]
)